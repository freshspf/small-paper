from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class PromptTemplateType(str, PyEnum):
    BASIC = "basic"
    INSTRUCTION_ENHANCED = "instruction_enhanced"
    CONTEXT_GUIDED = "context_guided"


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    template_type: Mapped[PromptTemplateType] = mapped_column(
        SQLEnum(PromptTemplateType, name="prompt_template_type"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    evaluation_tasks = relationship("EvaluationTask", back_populates="prompt_template")
