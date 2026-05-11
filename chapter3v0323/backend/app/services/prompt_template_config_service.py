from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template_config import PromptTemplateConfig
from app.schemas.prompt_template_config import PromptTemplateConfigCreate, PromptTemplateConfigUpdate


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHAPTER4_PROMPT_DIR = PROJECT_ROOT / "chapter4" / "prompts"


def _read_prompt_module(relative_path: str, fallback: str) -> str:
    path = CHAPTER4_PROMPT_DIR / relative_path
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return fallback


SWITCH_PROMPT_FRAGMENTS = {
    "count": _read_prompt_module(
        "modules/count_on.txt",
        "【数量限制】请控制输出规模，优先抽取文本中证据明确、语义稳定的核心术语和公理，避免无依据扩展。",
    ),
    "domain": "【领域提示】运行时将根据用户选择的 geography、medical 或 transportation 自动插入对应领域提示。",
    "naming": _read_prompt_module(
        "modules/naming_on.txt",
        "【命名规则】请使用规范、简洁、一致的英文 PascalCase 或 camelCase 命名，避免同义重复和冗余后缀。",
    ),
    "entity": _read_prompt_module(
        "modules/entity_on.txt",
        "【实体定义】请为关键概念保留清晰实体定义，区分类、属性、实例及其语义边界。",
    ),
}

DOMAIN_PROMPT_FRAGMENTS = {
    "geography": _read_prompt_module("modules/domain_geography.txt", SWITCH_PROMPT_FRAGMENTS["domain"]),
    "medical": _read_prompt_module("modules/domain_medical.txt", SWITCH_PROMPT_FRAGMENTS["domain"]),
    "transportation": _read_prompt_module("modules/domain_transportation.txt", SWITCH_PROMPT_FRAGMENTS["domain"]),
}


def list_prompt_template_configs(
    db: Session,
    template_name: Optional[str] = None,
    task_type: Optional[str] = None,
    template_type: Optional[str] = None,
    layer_name: Optional[str] = None,
) -> List[PromptTemplateConfig]:
    stmt = select(PromptTemplateConfig)
    if template_name:
        stmt = stmt.where(PromptTemplateConfig.templateName.like(f"%{template_name.strip()}%"))
    if task_type:
        stmt = stmt.where(PromptTemplateConfig.taskType == task_type.strip())
    if template_type:
        stmt = stmt.where(PromptTemplateConfig.templateType == template_type.strip())
    if layer_name:
        stmt = stmt.where(PromptTemplateConfig.layerName == layer_name.strip())

    stmt = stmt.order_by(
        PromptTemplateConfig.updatedTime.desc(),
        PromptTemplateConfig.id.desc(),
    )
    return list(db.scalars(stmt))


def get_prompt_template_config(db: Session, template_id: int) -> Optional[PromptTemplateConfig]:
    return db.get(PromptTemplateConfig, template_id)


def create_prompt_template_config(
    db: Session,
    payload: PromptTemplateConfigCreate,
) -> PromptTemplateConfig:
    template = PromptTemplateConfig(**payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_prompt_template_config(
    db: Session,
    template_id: int,
    payload: PromptTemplateConfigUpdate,
) -> Optional[PromptTemplateConfig]:
    template = db.get(PromptTemplateConfig, template_id)
    if template is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def delete_prompt_template_config(db: Session, template_id: int) -> bool:
    template = db.get(PromptTemplateConfig, template_id)
    if template is None:
        return False

    db.delete(template)
    db.commit()
    return True


def set_prompt_template_config_status(
    db: Session,
    template_id: int,
    status: int,
) -> Optional[PromptTemplateConfig]:
    template = db.get(PromptTemplateConfig, template_id)
    if template is None:
        return None
    template.status = status
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def build_prompt_preview(template: PromptTemplateConfig) -> dict[str, Any]:
    if template.taskType == "configuration_optimization" and template.templateType == "configurable":
        return build_configurable_prompt_preview(template)

    fragments = []
    if template.switchCount == 1:
        fragments.append(SWITCH_PROMPT_FRAGMENTS["count"])
    if template.switchDomain == 1:
        fragments.append(SWITCH_PROMPT_FRAGMENTS["domain"])
    if template.switchNaming == 1:
        fragments.append(SWITCH_PROMPT_FRAGMENTS["naming"])
    if template.switchEntity == 1:
        fragments.append(SWITCH_PROMPT_FRAGMENTS["entity"])

    switch_block = "\n".join(fragments)
    final_prompt = template.templateContent
    placeholder_names = [
        "{{SWITCH_MODULES}}",
        "{SWITCH_MODULES}",
        "{{CONSTRAINT_MODULES}}",
        "{CONSTRAINT_MODULES}",
    ]
    replaced = False
    for placeholder in placeholder_names:
        if placeholder in final_prompt:
            final_prompt = final_prompt.replace(placeholder, switch_block)
            replaced = True

    if not replaced and switch_block:
        final_prompt = f"{final_prompt.rstrip()}\n\n{switch_block}"

    return {
        "templateId": template.id,
        "templateName": template.templateName,
        "templateContent": template.templateContent,
        "switchModules": switch_block,
        "finalPrompt": final_prompt,
    }


def build_configurable_prompt_preview(template: PromptTemplateConfig, domain: str = "geography") -> dict[str, Any]:
    domain_fragment = DOMAIN_PROMPT_FRAGMENTS.get(domain, DOMAIN_PROMPT_FRAGMENTS["geography"])
    switch_fragments = {
        "COUNT_CONSTRAINT": SWITCH_PROMPT_FRAGMENTS["count"] if template.switchCount == 1 else "",
        "DOMAIN_HINT": domain_fragment if template.switchDomain == 1 else "",
        "NAMING_RULES": SWITCH_PROMPT_FRAGMENTS["naming"] if template.switchNaming == 1 else "",
        "ENTITY_DEFINITION": SWITCH_PROMPT_FRAGMENTS["entity"] if template.switchEntity == 1 else "",
    }
    final_prompt = template.templateContent
    for placeholder, value in switch_fragments.items():
        final_prompt = final_prompt.replace(f"{{{placeholder}}}", value)
        final_prompt = final_prompt.replace(f"{{{{{placeholder}}}}}", value)

    switch_block = "\n\n".join(fragment for fragment in switch_fragments.values() if fragment)
    return {
        "templateId": template.id,
        "templateName": template.templateName,
        "templateContent": template.templateContent,
        "switchModules": switch_block,
        "finalPrompt": final_prompt,
    }


def build_template_read(template: PromptTemplateConfig) -> dict[str, Any]:
    return {
        "id": template.id,
        "templateName": template.templateName,
        "taskType": template.taskType,
        "templateType": template.templateType,
        "layerName": template.layerName,
        "templateContent": template.templateContent,
        "switchCount": template.switchCount,
        "switchDomain": template.switchDomain,
        "switchNaming": template.switchNaming,
        "switchEntity": template.switchEntity,
        "remark": template.remark,
        "status": template.status,
        "createdTime": template.createdTime,
        "updatedTime": template.updatedTime,
    }
