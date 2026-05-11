from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import DatasetCreate, DatasetRead
from app.schemas.dataset_record import DatasetRecordRead
from app.services import dataset_service


router = APIRouter()


@router.get("/", response_model=List[DatasetRead])
async def list_datasets(db: Session = Depends(get_db)) -> List[DatasetRead]:
    return dataset_service.list_datasets(db)


@router.post("/", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> DatasetRead:
    return dataset_service.create_dataset(db, payload)


@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(default=None),
    source: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DatasetRead:
    try:
        return await dataset_service.ingest_uploaded_dataset(
            db=db,
            file=file,
            name=name,
            description=description,
            source=source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DatasetRead:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/records", response_model=List[DatasetRecordRead])
async def list_dataset_records(dataset_id: int, db: Session = Depends(get_db)) -> List[DatasetRecordRead]:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset_service.list_dataset_records(db, dataset_id)


@router.get("/{dataset_id}/preview", response_model=List[DatasetRecordRead])
async def preview_dataset_records(dataset_id: int, db: Session = Depends(get_db)) -> List[DatasetRecordRead]:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset_service.preview_dataset_records(db, dataset_id, limit=20)
