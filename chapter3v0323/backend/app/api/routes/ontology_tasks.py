from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ontology_task import OntologyBaselineCreate, OntologyLayeredCreate, OntologyTaskCreate
from app.services import ontology_task_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ontology_task(payload: OntologyTaskCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        task = ontology_task_service.create_and_run_ontology_task(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ok(ontology_task_service.build_task_read(db, task), "本体学习任务执行完成")


@router.post("/baseline", status_code=status.HTTP_201_CREATED)
async def create_baseline_task(
    background_tasks: BackgroundTasks,
    taskName: str = Form(...),
    modelId: int = Form(...),
    promptId: int = Form(...),
    domainType: str = Form(...),
    domainSwitch: int = Form(1),
    chunkMetadataSwitch: int = Form(1),
    remark: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        content = await file.read()
        if not content:
            raise ValueError("上传的 PDF 文件为空")
        payload = OntologyBaselineCreate(
            taskName=taskName,
            modelId=modelId,
            promptId=promptId,
            domainType=domainType,
            domainSwitch=domainSwitch,
            chunkMetadataSwitch=chunkMetadataSwitch,
            remark=remark,
        )
        task = ontology_task_service.create_baseline_task(db, payload, file.filename or "uploaded.pdf", content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(ontology_task_service.run_baseline_task_background, task.id)
    return ok(ontology_task_service.build_task_read(db, task), "baseline 任务已创建并开始执行")


@router.post("/layered", status_code=status.HTTP_201_CREATED)
async def create_layered_task(
    background_tasks: BackgroundTasks,
    taskName: str = Form(...),
    modelId: int = Form(...),
    semanticPromptId: int = Form(...),
    termPromptId: int = Form(...),
    conceptPromptId: int = Form(...),
    domainType: str = Form(...),
    domainSwitch: int = Form(1),
    chunkMetadataSwitch: int = Form(1),
    remark: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        content = await file.read()
        if not content:
            raise ValueError("上传的 PDF 文件为空")
        payload = OntologyLayeredCreate(
            taskName=taskName,
            modelId=modelId,
            semanticPromptId=semanticPromptId,
            termPromptId=termPromptId,
            conceptPromptId=conceptPromptId,
            domainType=domainType,
            domainSwitch=domainSwitch,
            chunkMetadataSwitch=chunkMetadataSwitch,
            remark=remark,
        )
        task = ontology_task_service.create_layered_task(db, payload, file.filename or "uploaded.pdf", content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(ontology_task_service.run_layered_task_background, task.id)
    return ok(ontology_task_service.build_task_read(db, task), "三层学习任务已创建并开始执行")


@router.post("/{task_id}/stop")
async def stop_ontology_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    task = ontology_task_service.stop_ontology_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="本体学习任务不存在")
    return ok(ontology_task_service.build_task_read(db, task), "已请求停止任务")


@router.get("")
@router.get("/")
async def list_ontology_tasks(
    taskName: Optional[str] = Query(default=None),
    taskType: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return ok(ontology_task_service.list_ontology_tasks(db, task_name=taskName, task_type=taskType))


@router.get("/{task_id}")
async def get_ontology_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    task = ontology_task_service.get_ontology_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="本体学习任务不存在")
    return ok(task)


@router.get("/{task_id}/stats")
async def get_ontology_task_stats(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    if ontology_task_service.get_ontology_task(db, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="本体学习任务不存在")
    return ok(ontology_task_service.get_task_stats(db, task_id))


@router.get("/{task_id}/chunks")
async def list_ontology_task_chunks(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    if ontology_task_service.get_ontology_task(db, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="本体学习任务不存在")
    return ok(ontology_task_service.list_task_chunks(db, task_id))


@router.get("/{task_id}/chunks/{chunk_id}")
async def get_ontology_chunk_detail(task_id: int, chunk_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    detail = ontology_task_service.get_chunk_detail(db, task_id, chunk_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chunk 不存在")
    return ok(detail)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_ontology_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = ontology_task_service.delete_ontology_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="本体学习任务不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
