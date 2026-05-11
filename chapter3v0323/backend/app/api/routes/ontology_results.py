from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import ontology_result_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.get("/tasks/{task_id}")
async def get_ontology_result(
    task_id: int,
    axiomType: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return ok(ontology_result_service.get_task_result(db, task_id, axiom_type=axiomType))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/export")
async def export_ontology_result(
    task_id: int,
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return ok(ontology_result_service.get_export_content(db, task_id, format))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/layers")
async def get_ontology_layers(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return ok(ontology_result_service.get_layer_results(db, task_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
