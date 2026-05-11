from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prompt_template_config import (
    PromptTemplateConfigCreate,
    PromptTemplateConfigRead,
    PromptTemplateConfigUpdate,
)
from app.services import prompt_template_config_service


router = APIRouter()


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


@router.get("")
@router.get("/")
async def list_prompt_template_configs(
    templateName: Optional[str] = Query(default=None),
    taskType: Optional[str] = Query(default=None),
    templateType: Optional[str] = Query(default=None),
    layerName: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    templates = prompt_template_config_service.list_prompt_template_configs(
        db,
        template_name=templateName,
        task_type=taskType,
        template_type=templateType,
        layer_name=layerName,
    )
    return ok([prompt_template_config_service.build_template_read(template) for template in templates])


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_prompt_template_config(
    payload: PromptTemplateConfigCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    template = prompt_template_config_service.create_prompt_template_config(db, payload)
    return ok(prompt_template_config_service.build_template_read(template), "提示词模板创建成功")


@router.get("/{template_id}")
async def get_prompt_template_config(
    template_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    template = prompt_template_config_service.get_prompt_template_config(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template config not found")
    return ok(prompt_template_config_service.build_template_read(template))


@router.put("/{template_id}")
async def update_prompt_template_config(
    template_id: int,
    payload: PromptTemplateConfigUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    template = prompt_template_config_service.update_prompt_template_config(db, template_id, payload)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template config not found")
    return ok(prompt_template_config_service.build_template_read(template), "提示词模板更新成功")


@router.put("/{template_id}/status")
async def update_prompt_template_config_status(
    template_id: int,
    status_value: int = Query(default=..., alias="status", ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    template = prompt_template_config_service.set_prompt_template_config_status(db, template_id, status_value)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template config not found")
    return ok(prompt_template_config_service.build_template_read(template), "提示词模板状态更新成功")


@router.get("/{template_id}/preview")
async def preview_prompt_template_config(
    template_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    template = prompt_template_config_service.get_prompt_template_config(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template config not found")
    return ok(prompt_template_config_service.build_prompt_preview(template))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_prompt_template_config(template_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = prompt_template_config_service.delete_prompt_template_config(db, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template config not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
