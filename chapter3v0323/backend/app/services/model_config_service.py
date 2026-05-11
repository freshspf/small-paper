from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate


def list_model_configs(db: Session) -> List[ModelConfig]:
    stmt = select(ModelConfig).order_by(ModelConfig.createdTime.desc(), ModelConfig.id.desc())
    return list(db.scalars(stmt))


def get_model_config(db: Session, config_id: int) -> Optional[ModelConfig]:
    return db.get(ModelConfig, config_id)


def create_model_config(db: Session, payload: ModelConfigCreate) -> ModelConfig:
    config = ModelConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_model_config(
    db: Session,
    config_id: int,
    payload: ModelConfigUpdate,
) -> Optional[ModelConfig]:
    config = db.get(ModelConfig, config_id)
    if config is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_model_config(db: Session, config_id: int) -> bool:
    config = db.get(ModelConfig, config_id)
    if config is None:
        return False

    db.delete(config)
    db.commit()
    return True
