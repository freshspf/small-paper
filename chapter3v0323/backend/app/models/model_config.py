from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ModelConfig(Base):
    __tablename__ = "model_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    modelName: Mapped[str] = mapped_column(String(50), nullable=False)
    modelCode: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    apiUrl: Mapped[str] = mapped_column(String(255), nullable=False)
    apiKey: Mapped[str] = mapped_column(String(255), nullable=False)
    temperature: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0.00, nullable=False)
    maxTokens: Mapped[int] = mapped_column(Integer, nullable=False)
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
