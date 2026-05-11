from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eval_task import EvalTaskCreate
from app.services import eval_task_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_eval_task(payload: EvalTaskCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        task = eval_task_service.create_eval_task(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ok(eval_task_service.build_task_read(db, task), "评估任务已创建")


@router.post("/{task_id}/start")
async def start_eval_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        task = eval_task_service.start_eval_task(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(eval_task_service.run_eval_task_background, task_id)
    return ok(eval_task_service.build_task_read(db, task), "评估任务已开始")


@router.post("/{task_id}/stop")
async def stop_eval_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        task = eval_task_service.stop_eval_task(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ok(eval_task_service.build_task_read(db, task), "评估任务已请求停止")


@router.get("")
@router.get("/")
async def list_eval_tasks(
    taskName: Optional[str] = Query(default=None),
    taskStatus: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return ok(eval_task_service.list_eval_tasks(db, task_name=taskName, task_status=taskStatus))


@router.get("/{task_id}")
async def get_eval_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    detail = eval_task_service.get_eval_task_detail(db, task_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估任务不存在")
    return ok(detail)


@router.get("/{task_id}/results")
async def list_eval_results(
    task_id: int,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    axiomType: Optional[str] = Query(default=None),
    trueLabel: Optional[int] = Query(default=None, ge=0, le=1),
    predictLabel: Optional[int] = Query(default=None, ge=0, le=1),
    runStatus: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if eval_task_service.get_eval_task_detail(db, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估任务不存在")
    return ok(
        eval_task_service.list_eval_results(
            db,
            task_id=task_id,
            page=page,
            page_size=pageSize,
            axiom_type=axiomType,
            true_label=trueLabel,
            predict_label=predictLabel,
            run_status=runStatus,
        )
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_eval_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = eval_task_service.delete_eval_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评估任务不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
