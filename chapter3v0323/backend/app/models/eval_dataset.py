from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class EvalDataset(Base):
    __tablename__ = "eval_dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    datasetName: Mapped[str] = mapped_column(String(100), nullable=False)
    fileName: Mapped[str] = mapped_column(String(255), nullable=False)
    recordCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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

    records = relationship("EvalDatasetRecord", back_populates="dataset", cascade="all, delete-orphan")
