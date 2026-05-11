from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetStatus
from app.models.dataset_record import DatasetRecord
from app.schemas.dataset import DatasetCreate


REQUIRED_DATASET_COLUMNS = {"id", "axiom_type", "axiom_text", "subject", "predicate", "object", "label", "source", "context_info"}


def list_datasets(db: Session) -> list[Dataset]:
    stmt = select(Dataset).order_by(Dataset.created_at.desc())
    return list(db.scalars(stmt))


def get_dataset(db: Session, dataset_id: int) -> Optional[Dataset]:
    return db.get(Dataset, dataset_id)


def create_dataset(db: Session, payload: DatasetCreate) -> Dataset:
    dataset = Dataset(name=payload.name, description=payload.description, source=payload.source, status=DatasetStatus.DRAFT)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def list_dataset_records(db: Session, dataset_id: int) -> list[DatasetRecord]:
    stmt = select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id).order_by(DatasetRecord.id.asc())
    return list(db.scalars(stmt))


def preview_dataset_records(db: Session, dataset_id: int, limit: int = 20) -> list[DatasetRecord]:
    stmt = (
        select(DatasetRecord)
        .where(DatasetRecord.dataset_id == dataset_id)
        .order_by(DatasetRecord.id.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


async def ingest_uploaded_dataset(
    db: Session,
    file: UploadFile,
    name: str,
    description: Optional[str],
    source: Optional[str],
) -> Dataset:
    extension = file.filename.split(".")[-1].lower() if file.filename else ""
    content = await file.read()

    if extension != "csv":
        raise ValueError("Only CSV files are supported for this demo.")

    rows = _parse_csv(content)

    if not rows:
        raise ValueError("Dataset file is empty.")

    _validate_dataset_rows(rows)

    dataset = Dataset(
        name=name,
        description=description,
        source=source,
        file_name=file.filename,
        row_count=len(rows),
        status=DatasetStatus.READY,
        has_labels=any(_normalize_nullable(row.get("label")) is not None for row in rows),
    )
    db.add(dataset)
    db.flush()

    for row in rows:
        db.add(
            DatasetRecord(
                dataset_id=dataset.id,
                sample_id=str(row["id"]),
                axiom_type=str(row["axiom_type"]),
                axiom_text=str(row["axiom_text"]),
                subject=_normalize_nullable(row.get("subject")),
                predicate=_normalize_nullable(row.get("predicate")),
                object_value=_normalize_nullable(row.get("object")),
                label=_parse_optional_int(row.get("label")),
                source=_normalize_nullable(row.get("source")),
                context_info=_normalize_nullable(row.get("context_info")),
            )
        )

    db.commit()
    db.refresh(dataset)
    return dataset


def _parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _parse_json(content: bytes) -> list[dict[str, Any]]:
    payload = json.loads(content.decode("utf-8-sig"))
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    raise ValueError("JSON dataset must be a list of objects.")


def _validate_dataset_rows(rows: list[dict[str, Any]]) -> None:
    missing = REQUIRED_DATASET_COLUMNS - set(rows[0].keys())
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")


def _normalize_nullable(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_optional_int(value: Any) -> Optional[int]:
    normalized = _normalize_nullable(value)
    if normalized is None:
        return None
    return int(float(normalized))
