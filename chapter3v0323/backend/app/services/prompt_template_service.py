from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateUpdate


def list_prompt_templates(db: Session) -> list[PromptTemplate]:
    stmt = select(PromptTemplate).order_by(PromptTemplate.created_at.asc())
    return list(db.scalars(stmt))


def get_prompt_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    return db.get(PromptTemplate, template_id)


def create_prompt_template(db: Session, payload: PromptTemplateCreate) -> PromptTemplate:
    if payload.is_default:
        _clear_default_template(db)

    template = PromptTemplate(**payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_prompt_template(
    db: Session,
    template_id: int,
    payload: PromptTemplateUpdate,
) -> Optional[PromptTemplate]:
    template = db.get(PromptTemplate, template_id)
    if template is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_default") is True:
        _clear_default_template(db)

    for field, value in update_data.items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def set_default_prompt_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    template = db.get(PromptTemplate, template_id)
    if template is None:
        return None

    _clear_default_template(db)
    template.is_default = True
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def _clear_default_template(db: Session) -> None:
    stmt = select(PromptTemplate)
    templates = list(db.scalars(stmt))
    for template in templates:
        if template.is_default:
            template.is_default = False
            db.add(template)
