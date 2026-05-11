from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.model_config import ModelConfigCreate, ModelConfigRead, ModelConfigUpdate
from app.services import model_config_service


router = APIRouter()


@router.get("/", response_model=List[ModelConfigRead])
async def list_model_configs(db: Session = Depends(get_db)) -> List[ModelConfigRead]:
    return model_config_service.list_model_configs(db)


@router.post("/", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    payload: ModelConfigCreate,
    db: Session = Depends(get_db),
) -> ModelConfigRead:
    try:
        return model_config_service.create_model_config(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model code already exists") from exc


@router.get("/{config_id}", response_model=ModelConfigRead)
async def get_model_config(config_id: int, db: Session = Depends(get_db)) -> ModelConfigRead:
    config = model_config_service.get_model_config(db, config_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model config not found")
    return config


@router.put("/{config_id}", response_model=ModelConfigRead)
async def update_model_config(
    config_id: int,
    payload: ModelConfigUpdate,
    db: Session = Depends(get_db),
) -> ModelConfigRead:
    try:
        config = model_config_service.update_model_config(db, config_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model code already exists") from exc

    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model config not found")
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_model_config(config_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = model_config_service.delete_model_config(db, config_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model config not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
