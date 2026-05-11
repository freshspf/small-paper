from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import eval_report_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.get("/tasks/{task_id}")
async def get_eval_report(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    report = eval_report_service.get_eval_report(db, task_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估任务不存在")
    return ok(report)
