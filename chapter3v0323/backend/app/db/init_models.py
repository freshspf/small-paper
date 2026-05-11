from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.llm_model import LLMModel


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_DIR = PROJECT_ROOT / "chapter3"
HARD_CASE_SCRIPTS_DIR = RESOURCE_DIR / "hard_case_scripts"


MODEL_NAME_PATTERN = re.compile(r'^MODEL_NAME\s*=\s*"([^"]+)"', re.MULTILINE)
API_KEY_PATTERN = re.compile(r'^OPENAI_API_KEY\s*=\s*"([^"]+)"', re.MULTILINE)
BASE_URL_PATTERN = re.compile(r'^OPENAI_BASE_URL\s*=\s*"([^"]+)"', re.MULTILINE)


def seed_llm_models(db: Session) -> None:
    for config in load_llm_configs():
        stmt = select(LLMModel).where(LLMModel.model_name == config["model_name"])
        existing = db.execute(stmt).scalar_one_or_none()

        if existing is None:
            db.add(LLMModel(**config))
            continue

        existing.name = config["name"]
        existing.provider = config["provider"]
        existing.base_url = config["base_url"]
        existing.api_key = config["api_key"]
        existing.model_name = config["model_name"]
        db.add(existing)

    db.commit()


def load_llm_configs() -> list[dict[str, object]]:
    configs: list[dict[str, object]] = []
    seen_model_names: set[str] = set()

    for path in sorted(HARD_CASE_SCRIPTS_DIR.glob("run_hard_case_*_context_guided.py")):
        text = path.read_text(encoding="utf-8")
        model_name = _search_required(MODEL_NAME_PATTERN, text, path)
        if model_name in seen_model_names:
            continue

        api_key = _search_required(API_KEY_PATTERN, text, path)
        base_url = _search_required(BASE_URL_PATTERN, text, path)
        seen_model_names.add(model_name)

        configs.append(
            {
                "name": _build_display_name(model_name),
                "provider": _infer_provider(model_name),
                "base_url": base_url,
                "api_key": api_key,
                "model_name": model_name,
                "is_default": model_name == "gpt-5.4",
            }
        )

    return configs


def _search_required(pattern: re.Pattern[str], text: str, path: Path) -> str:
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"Missing required config in {path.name}")
    return match.group(1).strip()


def _build_display_name(model_name: str) -> str:
    display_map = {
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "gpt-5.4": "GPT-5.4",
        "gpt-5-mini": "GPT-5 Mini",
        "qwen-max-0125": "Qwen Max",
        "Doubao-pro-128k": "Doubao Pro",
        "grok-4": "Grok 4",
        "llama-3.1-70b": "Llama 3.1 70B",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": "DeepSeek R1 Distill Qwen 32B",
        "ernie-4.5-turbo-128k": "ERNIE 4.5 Turbo",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
    }
    return display_map.get(model_name, model_name)


def _infer_provider(model_name: str) -> str:
    normalized = model_name.lower()
    if "claude" in normalized:
        return "Anthropic"
    if "gpt" in normalized:
        return "OpenAI"
    if "qwen" in normalized:
        return "Alibaba"
    if "doubao" in normalized:
        return "ByteDance"
    if "grok" in normalized:
        return "xAI"
    if "llama" in normalized:
        return "Meta"
    if "deepseek" in normalized:
        return "DeepSeek"
    if "ernie" in normalized:
        return "Baidu"
    if "gemini" in normalized:
        return "Google"
    return "Unknown"
