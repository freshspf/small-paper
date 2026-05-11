from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class PromptTemplateConfig(Base):
    __tablename__ = "prompt_template_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    templateName: Mapped[str] = mapped_column(String(50), nullable=False)
    taskType: Mapped[str] = mapped_column(String(50), nullable=False)
    templateType: Mapped[str] = mapped_column(String(30), nullable=False)
    layerName: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    templateContent: Mapped[str] = mapped_column(Text, nullable=False)
    switchCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchDomain: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchNaming: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchEntity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    createdTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updatedTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
