from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model_config import ModelConfig


DEFAULT_MODEL_CONFIGS = [
    {
        "modelName": "Claude Sonnet 4.6",
        "modelCode": "claude-sonnet-4-6",
        "apiUrl": "https://api2.aigcbest.top/v1",
        "apiKey": "sk-demo-claude",
        "temperature": 0.20,
        "maxTokens": 4096,
        "status": 1,
    },
    {
        "modelName": "GPT-5.4",
        "modelCode": "gpt-5.4",
        "apiUrl": "https://api2.aigcbest.top/v1",
        "apiKey": "sk-demo-openai",
        "temperature": 0.10,
        "maxTokens": 4096,
        "status": 1,
    },
    {
        "modelName": "Qwen Max",
        "modelCode": "qwen-max-0125",
        "apiUrl": "https://api2.aigcbest.top/v1",
        "apiKey": "sk-demo-qwen",
        "temperature": 0.20,
        "maxTokens": 4096,
        "status": 0,
    },
]


def seed_model_configs(db: Session) -> None:
    exists = db.scalar(select(ModelConfig.id).limit(1))
    if exists is not None:
        return

    for item in DEFAULT_MODEL_CONFIGS:
        db.add(ModelConfig(**item))
    db.commit()
