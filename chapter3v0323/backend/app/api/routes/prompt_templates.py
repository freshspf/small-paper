from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateRead, PromptTemplateUpdate
from app.services import prompt_template_service


router = APIRouter()


@router.get("/", response_model=list[PromptTemplateRead])
async def list_prompt_templates(db: Session = Depends(get_db)) -> list[PromptTemplateRead]:
    return prompt_template_service.list_prompt_templates(db)


@router.post("/", response_model=PromptTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_prompt_template(
    payload: PromptTemplateCreate,
    db: Session = Depends(get_db),
) -> PromptTemplateRead:
    return prompt_template_service.create_prompt_template(db, payload)


@router.get("/{template_id}", response_model=PromptTemplateRead)
async def get_prompt_template(template_id: int, db: Session = Depends(get_db)) -> PromptTemplateRead:
    template = prompt_template_service.get_prompt_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found")
    return template


@router.put("/{template_id}", response_model=PromptTemplateRead)
async def update_prompt_template(
    template_id: int,
    payload: PromptTemplateUpdate,
    db: Session = Depends(get_db),
) -> PromptTemplateRead:
    template = prompt_template_service.update_prompt_template(db, template_id, payload)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found")
    return template


@router.put("/{template_id}/set-default", response_model=PromptTemplateRead)
async def set_default_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
) -> PromptTemplateRead:
    template = prompt_template_service.set_default_prompt_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found")
    return template
