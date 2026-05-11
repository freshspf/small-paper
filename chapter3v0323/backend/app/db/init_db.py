from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.models.prompt_template import PromptTemplate, PromptTemplateType


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_DIR = PROJECT_ROOT / "chapter3"
PROMPTS_DIR = RESOURCE_DIR / "prompts"


def _read_prompt_file(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


DEFAULT_PROMPT_TEMPLATES = [
    {
        "name": "基础型提示词",
        "template_type": PromptTemplateType.BASIC,
        "content": _read_prompt_file("basic_prompt.txt"),
        "description": "适用于基础判断任务的最小提示模板。",
        "is_builtin": True,
        "is_default": False,
        "is_active": True,
    },
    {
        "name": "指令增强型提示词",
        "template_type": PromptTemplateType.INSTRUCTION_ENHANCED,
        "content": _read_prompt_file("instruction_enhanced_prompt"),
        "description": "加入推理步骤要求，提升判断稳定性。",
        "is_builtin": True,
        "is_default": False,
        "is_active": True,
    },
    {
        "name": "上下文引导型提示词",
        "template_type": PromptTemplateType.CONTEXT_GUIDED,
        "content": _read_prompt_file("context_guided_prompt"),
        "description": "引入上下文知识进行语义分析与判断。",
        "is_builtin": True,
        "is_default": True,
        "is_active": True,
    },
]


def seed_prompt_templates(db: Session) -> None:
    for item in DEFAULT_PROMPT_TEMPLATES:
        stmt = select(PromptTemplate).where(PromptTemplate.name == item["name"])
        existing = db.execute(stmt).scalar_one_or_none()

        if existing is None:
            db.add(PromptTemplate(**item))
            continue

        existing.template_type = item["template_type"]
        existing.content = item["content"]
        existing.description = item["description"]
        existing.is_builtin = item["is_builtin"]
        existing.is_default = item["is_default"]
        existing.is_active = item["is_active"]

    db.commit()
