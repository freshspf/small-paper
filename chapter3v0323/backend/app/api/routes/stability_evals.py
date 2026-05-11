from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import stability_eval_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.get("/templates")
async def get_templates() -> dict[str, Any]:
    return ok(stability_eval_service.get_perturbation_templates())


@router.post("/tasks/{base_task_id}/run", status_code=status.HTTP_201_CREATED)
async def create_stability_eval_task(
    base_task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        task = stability_eval_service.create_stability_eval_task(db, base_task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(stability_eval_service.run_stability_eval_background, task.id)
    return ok(stability_eval_service.build_task_read(task), "稳定性评估任务已开始")


@router.post("/tasks/{stability_task_id}/stop")
async def stop_stability_eval_task(stability_task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        task = stability_eval_service.stop_stability_eval_task(db, stability_task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ok(stability_eval_service.build_task_read(task), "稳定性评估任务已请求停止")


@router.get("/base-tasks/{base_task_id}/tasks")
async def list_stability_tasks(base_task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ok(stability_eval_service.list_stability_tasks(db, base_task_id))


@router.get("/tasks/{stability_task_id}")
async def get_stability_task(stability_task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    task = stability_eval_service.get_stability_task_detail(db, stability_task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="稳定性评估任务不存在")
    return ok(task)


@router.get("/tasks/{stability_task_id}/records")
async def list_stability_records(
    stability_task_id: int,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return ok(stability_eval_service.list_stability_records(db, stability_task_id, page=page, page_size=pageSize))


@router.get("/tasks/{stability_task_id}/dataset")
async def list_perturbed_dataset(stability_task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    return ok(stability_eval_service.list_perturbed_dataset(db, stability_task_id))
