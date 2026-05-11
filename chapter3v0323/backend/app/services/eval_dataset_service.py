from __future__ import annotations

import csv
import io
from typing import Any, Optional

from fastapi import UploadFile
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.eval_dataset import EvalDataset
from app.models.eval_dataset_record import EvalDatasetRecord


REQUIRED_COLUMNS = {
    "axiom_type",
    "subject",
    "predicate",
    "object",
    "label",
    "source",
    "axiom_text",
}
OPTIONAL_COLUMNS = {
    "negative_strategy",
    "subject_context",
    "object_context",
    "context_info",
}


def list_eval_datasets(db: Session, dataset_name: Optional[str] = None) -> list[EvalDataset]:
    stmt = select(EvalDataset)
    if dataset_name:
        stmt = stmt.where(EvalDataset.datasetName.like(f"%{dataset_name.strip()}%"))
    stmt = stmt.order_by(EvalDataset.createdTime.desc(), EvalDataset.id.desc())
    return list(db.scalars(stmt))


def get_eval_dataset(db: Session, dataset_id: int) -> Optional[EvalDataset]:
    return db.get(EvalDataset, dataset_id)


def delete_eval_dataset(db: Session, dataset_id: int) -> bool:
    dataset = db.get(EvalDataset, dataset_id)
    if dataset is None:
        return False
    db.delete(dataset)
    db.commit()
    return True


def list_eval_dataset_records(
    db: Session,
    dataset_id: int,
    page: int = 1,
    page_size: int = 20,
    axiom_type: Optional[str] = None,
    label: Optional[int] = None,
    source: Optional[str] = None,
) -> tuple[list[EvalDatasetRecord], int]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    stmt = select(EvalDatasetRecord).where(EvalDatasetRecord.datasetId == dataset_id)
    stmt = _apply_record_filters(stmt, axiom_type=axiom_type, label=label, source=source)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    stmt = stmt.order_by(EvalDatasetRecord.id.asc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt)), total


async def ingest_uploaded_eval_dataset(
    db: Session,
    dataset_name: str,
    remark: Optional[str],
    file: UploadFile,
) -> dict[str, Any]:
    normalized_name = dataset_name.strip() if dataset_name else ""
    if not normalized_name:
        raise ValueError("数据集名称不能为空。")
    if file is None or not file.filename:
        raise ValueError("上传文件不能为空。")
    if not file.filename.lower().endswith(".csv"):
        raise ValueError("文件类型错误：仅支持 .csv 文件。")

    content = await file.read()
    if not content:
        raise ValueError("CSV 文件为空。")

    rows = _parse_csv(content)
    if not rows:
        raise ValueError("CSV 文件没有可导入的数据行。")

    _validate_header(rows[0])
    parsed_records = _parse_records(rows)

    dataset = EvalDataset(
        datasetName=normalized_name,
        fileName=file.filename,
        recordCount=len(parsed_records),
        remark=_normalize_nullable(remark),
    )

    try:
        db.add(dataset)
        db.flush()
        for record in parsed_records:
            db.add(EvalDatasetRecord(datasetId=dataset.id, **record))
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        raise

    return {
        "dataset": dataset,
        "totalCount": len(rows),
        "successCount": len(parsed_records),
        "failedCount": 0,
        "errors": [],
    }


def build_record_read(record: EvalDatasetRecord, include_context: bool = False) -> dict[str, Any]:
    context_info = record.contextInfo or ""
    context_summary = _truncate_text(context_info, 120)
    return {
        "id": record.id,
        "datasetId": record.datasetId,
        "axiomType": record.axiomType,
        "subject": record.subject,
        "predicate": record.predicate,
        "object": record.object,
        "label": record.label,
        "source": record.source,
        "axiomText": record.axiomText,
        "negativeStrategy": record.negativeStrategy,
        "subjectContext": record.subjectContext if include_context else _truncate_text(record.subjectContext, 160),
        "objectContext": record.objectContext if include_context else _truncate_text(record.objectContext, 160),
        "contextInfo": context_info if include_context else None,
        "contextSummary": context_summary,
        "createdTime": record.createdTime,
        "updatedTime": record.updatedTime,
    }


def build_dataset_read(dataset: EvalDataset) -> dict[str, Any]:
    return {
        "id": dataset.id,
        "datasetName": dataset.datasetName,
        "fileName": dataset.fileName,
        "recordCount": dataset.recordCount,
        "remark": dataset.remark,
        "createdTime": dataset.createdTime,
        "updatedTime": dataset.updatedTime,
    }


def _apply_record_filters(
    stmt: Select[tuple[EvalDatasetRecord]],
    axiom_type: Optional[str],
    label: Optional[int],
    source: Optional[str],
) -> Select[tuple[EvalDatasetRecord]]:
    if axiom_type:
        stmt = stmt.where(EvalDatasetRecord.axiomType == axiom_type.strip())
    if label is not None:
        stmt = stmt.where(EvalDatasetRecord.label == label)
    if source:
        stmt = stmt.where(EvalDatasetRecord.source.like(f"%{source.strip()}%"))
    return stmt


def _parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = _decode_csv(content)
    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV 文件缺少表头。")
        return [dict(row) for row in reader if _has_non_empty_value(row)]
    except csv.Error as exc:
        raise ValueError(f"CSV 解析失败：{exc}") from exc


def _decode_csv(content: bytes) -> str:
    if content.startswith(b"PK\x03\x04"):
        raise ValueError("上传文件实际是 Excel 工作簿格式，请另存为 CSV UTF-8（逗号分隔）后再上传。")

    bom_encodings = [
        (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xff\xfe", "utf-16"),
        (b"\xfe\xff", "utf-16"),
    ]
    for bom, encoding in bom_encodings:
        if content.startswith(bom):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                break

    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = content.decode(encoding)
            if _looks_like_csv_text(text):
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("CSV 编码解析失败，请使用 UTF-8、GB18030、GBK 或 UTF-16 编码。")


def _looks_like_csv_text(text: str) -> bool:
    sample = text[:2048]
    if "\x00" in sample:
        return False
    return "," in sample or "\t" in sample or "\n" in sample


def _has_non_empty_value(row: dict[str, Any]) -> bool:
    return any(str(value).strip() for value in row.values() if value is not None)


def _validate_header(first_row: dict[str, Any]) -> None:
    columns = {str(column).strip() for column in first_row.keys() if column is not None}
    missing_columns = REQUIRED_COLUMNS - columns
    if missing_columns:
        missing_text = "、".join(sorted(missing_columns))
        raise ValueError(f"CSV 缺少必填字段：{missing_text}。")


def _parse_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed_records = []
    errors = []

    for row_index, row in enumerate(rows, start=2):
        try:
            parsed_records.append(_parse_record(row, row_index))
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        preview_errors = errors[:20]
        more = "" if len(errors) <= 20 else f"；另有 {len(errors) - 20} 条错误未展示"
        raise ValueError("CSV 数据校验失败：" + "；".join(preview_errors) + more)

    return parsed_records


def _parse_record(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    required_values = {
        "axiom_type": _normalize_required(row.get("axiom_type"), "axiom_type", row_index),
        "subject": _normalize_required(row.get("subject"), "subject", row_index),
        "predicate": _normalize_required(row.get("predicate"), "predicate", row_index),
        "object": _normalize_required(row.get("object"), "object", row_index),
        "source": _normalize_required(row.get("source"), "source", row_index),
        "axiom_text": _normalize_required(row.get("axiom_text"), "axiom_text", row_index),
    }
    label = _parse_label(row.get("label"), row_index)

    return {
        "axiomType": required_values["axiom_type"],
        "subject": required_values["subject"],
        "predicate": required_values["predicate"],
        "object": required_values["object"],
        "label": label,
        "source": required_values["source"],
        "axiomText": required_values["axiom_text"],
        "negativeStrategy": _normalize_nullable(row.get("negative_strategy")),
        "subjectContext": _normalize_nullable(row.get("subject_context")),
        "objectContext": _normalize_nullable(row.get("object_context")),
        "contextInfo": _normalize_nullable(row.get("context_info")),
    }


def _normalize_required(value: Any, field_name: str, row_index: int) -> str:
    normalized = _normalize_nullable(value)
    if normalized is None:
        raise ValueError(f"第 {row_index} 行字段 {field_name} 不能为空")
    return normalized


def _normalize_nullable(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_label(value: Any, row_index: int) -> int:
    normalized = _normalize_nullable(value)
    if normalized is None:
        raise ValueError(f"第 {row_index} 行字段 label 不能为空")
    if normalized not in {"0", "1"}:
        raise ValueError(f"第 {row_index} 行字段 label 只能为 0 或 1")
    return int(normalized)


def _truncate_text(value: Optional[str], max_length: int) -> Optional[str]:
    if not value:
        return value
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."
