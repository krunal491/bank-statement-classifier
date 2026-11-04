"""
Step 1 of the pipeline: read the PDF.

For every page we decide whether it is a TEXT page (the PDF already contains
the words) or an IMAGE page (a scan/photo, so we need OCR).

Whatever the page type, we return the same simple structure: a list of
"words", where each word knows its text and its position on the page.
Later steps only work with these words, so they don't care whether the
page was scanned or not.

    Word = {"text": "500.00", "x0": 410, "x1": 450, "top": 120, "bottom": 130}
"""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import cv2
import pymupdf as fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

from src.layout import group_into_lines

# A page with fewer characters than this is treated as a scanned image.
MIN_TEXT_CHARS = 30
# Resolution used when turning a scanned page into an image for OCR.
OCR_DPI = 300
# PyMuPDF calls must not overlap across API worker threads.
_pdf_lock = Lock()


class PasswordRequiredError(Exception):
    """Raised when the PDF is locked and no (or a wrong) password was given."""


def open_pdf(pdf_bytes, password=None):
    """Open a PDF from bytes. Unlocks it if it is password protected."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise PasswordRequiredError(
                "This PDF is password protected. Please enter the correct password."
            )
    return doc


def detect_page_type(page):
    """Return 'text' if the page has real text, otherwise 'image'."""
    text = page.get_text("text").strip()
    return "text" if len(text) >= MIN_TEXT_CHARS else "image"


def detect_pdf_type(page_types):
    """Summarise the page types: 'text', 'image' or 'mixed'."""
    unique = set(page_types)
    if unique == {"text"}:
        return "text"
    if unique == {"image"}:
        return "image"
    return "mixed"


# ---------------------------------------------------------------------------
# Text pages
# ---------------------------------------------------------------------------
def words_from_text_page(page):
    """Get words with positions straight from the PDF (fast and exact)."""
    words = []
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        words.append({"text": text, "x0": x0, "x1": x1, "top": y0, "bottom": y1})
    return words


# ---------------------------------------------------------------------------
# Image pages (OCR)
# ---------------------------------------------------------------------------
def page_to_image(page, dpi=OCR_DPI):
    """Render a PDF page as a grayscale numpy image."""
    # Render straight to grayscale and read the raw samples buffer directly -
    # going through a PNG encode/decode round trip here cost over 1s per page.
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    return np.array(image)


def deskew(image):
    """
    Straighten a slightly rotated scan.

    We find all dark pixels, fit the smallest rotated rectangle around them
    and rotate the image back by that angle.
    """
    inverted = cv2.bitwise_not(image)
    _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    # OpenCV returns angles in different ranges depending on the version.
    if angle > 45:
        angle -= 90
    elif angle < -45:
        angle += 90
    if abs(angle) < 0.1 or abs(angle) > 10:  # nothing to fix / not a small tilt
        return image
    h, w = image.shape
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), -angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_for_ocr(image):
    """Clean up a scan so Tesseract reads it better: straighten, denoise, binarise."""
    image = deskew(image)
    image = cv2.medianBlur(image, 3)  # removes salt-and-pepper noise
    _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return image


def words_from_image(image):
    """Run OCR on an already-rendered page image and return words with positions."""
    image = preprocess_for_ocr(image)
    # psm 6 = "assume a single uniform block of text", which works well for tables.
    data = pytesseract.image_to_data(
        image, config="--psm 6", output_type=pytesseract.Output.DICT
    )
    # Convert pixel positions to PDF points so both page types use the same scale.
    scale = 72 / OCR_DPI
    words = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text or float(data["conf"][i]) < 0:
            continue
        left, top = data["left"][i] * scale, data["top"][i] * scale
        width, height = data["width"][i] * scale, data["height"][i] * scale
        words.append(
            {"text": text, "x0": left, "x1": left + width, "top": top, "bottom": top + height}
        )
    return words


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def read_pdf(pdf_bytes, password=None):
    """
    Read every page of the PDF.

    Returns a dict:
        {
          "pdf_type": "text" | "image" | "mixed",
          "pages": [ {"number": 1, "type": "text", "words": [...]}, ... ],
          "full_text": "all text joined together (used to find account details)"
        }
    """
    pages = []
    # Bound rendered images to two at a time instead of retaining every 300-DPI
    # page of a long statement in memory. OCR workers only receive numpy arrays.
    workers = min(os.cpu_count() or 1, 2)
    with _pdf_lock, open_pdf(pdf_bytes, password) as doc:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending = []
            for index, page in enumerate(doc):
                page_type = detect_page_type(page)
                entry = {"number": index + 1, "type": page_type, "words": []}
                if page_type == "text":
                    entry["words"] = words_from_text_page(page)
                else:
                    pending.append((entry, pool.submit(words_from_image, page_to_image(page))))
                pages.append(entry)
                if len(pending) == workers:
                    for target, future in pending:
                        target["words"] = future.result()
                    pending.clear()
            for target, future in pending:
                target["words"] = future.result()

    full_text = "\n".join(
        line["text"] for page in pages for line in group_into_lines(page["words"])
    )
    return {
        "pdf_type": detect_pdf_type([p["type"] for p in pages]),
        "pages": pages,
        "full_text": full_text,
    }
