"""
Turn loose words into lines of text.

Words that sit at (roughly) the same height on the page belong to the same
line. This works the same way for real text PDFs and for OCR output.
"""

from statistics import median


def group_into_lines(words):
    """
    Group words into lines, top to bottom, each line sorted left to right.

    Returns a list of {"text": "...", "words": [...], "top": y}.
    """
    if not words:
        return []

    heights = [w["bottom"] - w["top"] for w in words if w["bottom"] > w["top"]]
    # Two words are on the same line if their vertical centres are closer
    # than about half a text height.
    tolerance = (median(heights) if heights else 8) * 0.55

    sorted_words = sorted(words, key=lambda w: (w["top"] + w["bottom"]) / 2)
    lines = []
    current = [sorted_words[0]]
    current_centre = _centre(sorted_words[0])

    for word in sorted_words[1:]:
        if abs(_centre(word) - current_centre) <= tolerance:
            current.append(word)
            # keep a running average so slightly tilted lines still group well
            current_centre = sum(_centre(w) for w in current) / len(current)
        else:
            lines.append(_make_line(current))
            current = [word]
            current_centre = _centre(word)
    lines.append(_make_line(current))
    return lines


def _centre(word):
    return (word["top"] + word["bottom"]) / 2


def _make_line(words):
    words = sorted(words, key=lambda w: w["x0"])
    return {
        "text": " ".join(w["text"] for w in words),
        "words": words,
        "top": min(w["top"] for w in words),
    }
