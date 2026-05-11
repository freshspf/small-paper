from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.llm_model import LLMModel
from app.schemas.llm_model import LLMModelCreate, LLMModelUpdate


def list_models(db: Session) -> List[LLMModel]:
    stmt = select(LLMModel).order_by(LLMModel.created_at.desc())
    return list(db.scalars(stmt))


def get_model(db: Session, model_id: int) -> Optional[LLMModel]:
    return db.get(LLMModel, model_id)


def create_model(db: Session, payload: LLMModelCreate) -> LLMModel:
    if payload.is_default:
        _clear_default_flag(db)

    model = LLMModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model(db: Session, model_id: int, payload: LLMModelUpdate) -> Optional[LLMModel]:
    model = db.get(LLMModel, model_id)
    if model is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_default") is True:
        _clear_default_flag(db, exclude_id=model_id)

    for field, value in update_data.items():
        setattr(model, field, value)

    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int) -> bool:
    model = db.get(LLMModel, model_id)
    if model is None:
        return False

    db.delete(model)
    db.commit()
    return True


def _clear_default_flag(db: Session, exclude_id: Optional[int] = None) -> None:
    stmt = update(LLMModel).values(is_default=False)
    if exclude_id is not None:
        stmt = stmt.where(LLMModel.id != exclude_id)
    db.execute(stmt)
