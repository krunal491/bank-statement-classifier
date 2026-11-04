import logging
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from backend import ml_eval
from backend.json_safe import df_records, dict_clean
from src.classifier.categories import ALL_CATEGORIES
from src.classifier.hybrid import save_corrections
from src.classifier.ml_model import CORRECTIONS_FILE
from src.exporter import to_csv_bytes, to_excel_bytes
from src.pdf_reader import PasswordRequiredError
from src.pipeline import combined_report, process_many, reclassify

logger = logging.getLogger(__name__)
MAX_PDF_BYTES = 20 * 1024 * 1024

CATEGORIES = sorted(ALL_CATEGORIES + ["Others"])

router = APIRouter(prefix="/api", tags=["statements"])


@router.get("/health")
def health():
    """Cheap liveness probe (also what Render's health check hits)."""
    return {"status": "ok"}


@router.post("/process")
def process(
    files: List[UploadFile] = File(default=[]),
    password: str = Form(default=""),
):
    if len(files) != 1:
        raise HTTPException(400, "Upload exactly one PDF statement at a time.")
    file = files[0]
    data = file.file.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(413, "Choose a PDF smaller than 20 MB.")
    if not data:
        raise HTTPException(400, "The selected PDF is empty.")
    file_tuples = [(file.filename, data, password or None)]

    try:
        output = process_many(file_tuples)
    except PasswordRequiredError as error:
        raise HTTPException(423, str(error))
    except Exception:  # Keep internal exception details out of the response.
        raise HTTPException(422, "This PDF could not be read. Please check the file and try again.")

    merged = output["merged"]
    if merged.empty:
        raise HTTPException(422, "No transactions were found. Is this a bank statement with a transaction table?")

    results = [
        {"account": dict_clean(r["account"]), "report": dict_clean(r["report"])}
        for r in output["results"]
    ]
    report = dict_clean(combined_report(output["results"], merged))
    return {
        "results": results,
        "table": df_records(merged),
        "report": report,
        "duplicatesRemoved": output["duplicates_removed"],
        "categories": CATEGORIES,
    }


class CorrectionRow(BaseModel):
    description: str
    direction: Optional[str] = None
    category: str


class CorrectionsRequest(BaseModel):
    table: List[dict]
    corrections: List[CorrectionRow]


@router.post("/corrections")
def corrections(payload: CorrectionsRequest):
    if not payload.table:
        raise HTTPException(400, "No table to reclassify.")
    df = pd.DataFrame(payload.table)
    rows = [r.model_dump() for r in payload.corrections]
    total = save_corrections(rows)
    updated = reclassify(df)
    return {"table": df_records(updated), "correctionsTotal": total}


@router.get("/model/insights")
def model_insights():
    """Powers the 'Model insights' tab: accuracy on synthetic data the model never
    trained on, so it's an honest number rather than one that always looks good."""
    corrections_count = 0
    if CORRECTIONS_FILE.exists():
        corrections_count = len(pd.read_csv(CORRECTIONS_FILE))
    try:
        baseline = ml_eval.baseline_eval()
    except (OSError, ValueError, KeyError):
        logger.exception("Model evaluation artifact is unavailable")
        raise HTTPException(503, "Model insights are temporarily unavailable. Please try again.")
    return {"correctionsCount": corrections_count, "baseline": baseline}


class ExportRequest(BaseModel):
    table: List[dict]
    account: dict
    report: dict


@router.post("/export/excel")
def export_excel(payload: ExportRequest):
    df = pd.DataFrame(payload.table)
    data = to_excel_bytes(df, payload.account, payload.report)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=classified_transactions.xlsx"},
    )


class CsvExportRequest(BaseModel):
    table: List[dict]


@router.post("/export/csv")
def export_csv(payload: CsvExportRequest):
    df = pd.DataFrame(payload.table)
    data = to_csv_bytes(df)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=classified_transactions.csv"},
    )
