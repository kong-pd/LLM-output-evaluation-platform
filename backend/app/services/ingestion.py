import csv
import io
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.database import Dataset, EvalItem, generate_id

REQUIRED_COLUMNS = {"question", "llm_answer"}
OPTIONAL_COLUMNS = {"context"}
COLUMN_ALIASES = {
    "answer": "llm_answer", "response": "llm_answer",
    "llm_response": "llm_answer", "output": "llm_answer", "llm_output": "llm_answer",
}


@dataclass
class IngestionResult:
    dataset: Dataset
    rows_imported: int
    warnings: list[str]


class IngestionError(Exception):
    pass


def _normalize_columns(raw_headers):
    mapping = {}
    for raw in raw_headers:
        clean = raw.strip().lower().replace(" ", "_")
        if clean in (REQUIRED_COLUMNS | OPTIONAL_COLUMNS):
            mapping[clean] = raw
        elif clean in COLUMN_ALIASES:
            mapping[COLUMN_ALIASES[clean]] = raw
    return mapping


def ingest_csv(file_bytes, filename, db: Session):
    warnings = []
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
        warnings.append("File was not UTF-8; decoded as Latin-1.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise IngestionError("CSV file appears to be empty or has no header row.")

    col_map = _normalize_columns(list(reader.fieldnames))
    missing = REQUIRED_COLUMNS - set(col_map.keys())
    if missing:
        raise IngestionError(f"Missing required columns: {', '.join(sorted(missing))}. Found: {', '.join(reader.fieldnames)}")

    has_context = "context" in col_map
    dataset = Dataset(id=generate_id(), name=filename)
    db.add(dataset)

    rows_imported = 0
    for idx, row in enumerate(reader):
        question = (row.get(col_map["question"]) or "").strip()
        llm_answer = (row.get(col_map["llm_answer"]) or "").strip()
        context = (row.get(col_map.get("context", ""), "") or "").strip() if has_context else ""
        if not question and not llm_answer:
            continue
        db.add(EvalItem(id=generate_id(), dataset_id=dataset.id, row_index=idx, question=question, context=context, llm_answer=llm_answer))
        rows_imported += 1

    if rows_imported == 0:
        raise IngestionError("No valid rows found in CSV.")

    dataset.total_items = rows_imported
    db.commit()
    db.refresh(dataset)
    return IngestionResult(dataset=dataset, rows_imported=rows_imported, warnings=warnings)
