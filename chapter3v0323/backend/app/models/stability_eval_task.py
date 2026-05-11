from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DECIMAL, Integer, String, TIMESTAMP, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class StabilityEvalTask(Base):
    __tablename__ = "stability_eval_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baseTaskId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    axiomTypeScope: Mapped[str] = mapped_column(String(255), nullable=False)
    templateCount: Mapped[int] = mapped_column(Integer, server_default=text("5"), nullable=False)
    taskStatus: Mapped[str] = mapped_column(String(20), server_default="running", nullable=False, index=True)
    totalCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    successCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    failCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    hardConsistency: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4), nullable=True)
    softConsistency: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
