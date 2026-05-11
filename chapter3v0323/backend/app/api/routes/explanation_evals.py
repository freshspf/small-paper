from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.explanation_eval import ExplanationEvalUpsert
from app.services import explanation_eval_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.get("/tasks/{task_id}/records")
async def list_explanation_eval_records(
    task_id: int,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    annotationStatus: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        data = explanation_eval_service.list_explanation_eval_items(
            db,
            task_id=task_id,
            page=page,
            page_size=pageSize,
            annotation_status=annotationStatus,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ok(data)


@router.get("/tasks/{task_id}/stats")
async def get_explanation_eval_stats(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        data = explanation_eval_service.get_explanation_eval_stats(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ok(data)


@router.get("/results/{result_id}")
async def get_explanation_eval_detail(result_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    data = explanation_eval_service.get_explanation_eval_detail(db, result_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="解释评估记录不存在或样本不满足标注条件")
    return ok(data)


@router.post("/records")
async def upsert_explanation_eval_record(
    payload: ExplanationEvalUpsert,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        annotation = explanation_eval_service.upsert_explanation_eval_record(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ok(explanation_eval_service.build_annotation_read(annotation), "解释标注已保存")
