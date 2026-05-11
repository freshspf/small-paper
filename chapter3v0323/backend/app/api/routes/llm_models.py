from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.llm_model import LLMModelCreate, LLMModelRead, LLMModelUpdate
from app.services import llm_model_service


router = APIRouter()


@router.get("/", response_model=List[LLMModelRead])
async def list_models(db: Session = Depends(get_db)) -> List[LLMModelRead]:
    return llm_model_service.list_models(db)


@router.post("/", response_model=LLMModelRead, status_code=status.HTTP_201_CREATED)
async def create_model(payload: LLMModelCreate, db: Session = Depends(get_db)) -> LLMModelRead:
    return llm_model_service.create_model(db, payload)


@router.get("/{model_id}", response_model=LLMModelRead)
async def get_model(model_id: int, db: Session = Depends(get_db)) -> LLMModelRead:
    model = llm_model_service.get_model(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=LLMModelRead)
async def update_model(model_id: int, payload: LLMModelUpdate, db: Session = Depends(get_db)) -> LLMModelRead:
    model = llm_model_service.update_model(db, model_id, payload)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_model(model_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = llm_model_service.delete_model(db, model_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
