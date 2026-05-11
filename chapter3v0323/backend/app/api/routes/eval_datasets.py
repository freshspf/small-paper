from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import eval_dataset_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_eval_dataset(
    datasetName: str = Form(...),
    remark: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = await eval_dataset_service.ingest_uploaded_eval_dataset(
            db=db,
            dataset_name=datasetName,
            remark=remark,
            file=file,
        )
        result["dataset"] = eval_dataset_service.build_dataset_read(result["dataset"])
        return ok(result, "数据集导入成功")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/")
async def list_eval_datasets(
    datasetName: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    datasets = eval_dataset_service.list_eval_datasets(db, dataset_name=datasetName)
    return ok([eval_dataset_service.build_dataset_read(dataset) for dataset in datasets])


@router.get("/{dataset_id}")
async def get_eval_dataset(dataset_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    dataset = eval_dataset_service.get_eval_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")
    return ok(eval_dataset_service.build_dataset_read(dataset))


@router.get("/{dataset_id}/records")
async def list_eval_dataset_records(
    dataset_id: int,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    axiomType: Optional[str] = Query(default=None),
    label: Optional[int] = Query(default=None, ge=0, le=1),
    source: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    dataset = eval_dataset_service.get_eval_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")

    records, total = eval_dataset_service.list_eval_dataset_records(
        db=db,
        dataset_id=dataset_id,
        page=page,
        page_size=pageSize,
        axiom_type=axiomType,
        label=label,
        source=source,
    )
    return ok(
        {
            "records": [eval_dataset_service.build_record_read(record, include_context=True) for record in records],
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_eval_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = eval_dataset_service.delete_eval_dataset(db, dataset_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
