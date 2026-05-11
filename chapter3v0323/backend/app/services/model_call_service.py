from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Optional

from app.models.model_config import ModelConfig


def call_openai_compatible_model(model: ModelConfig, prompt: str) -> tuple[str, Optional[int], Optional[float]]:
    payload = {
        "model": model.modelCode,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(model.temperature),
        "max_tokens": model.maxTokens,
    }
    request = urllib.request.Request(
        url=f"{model.apiUrl.rstrip('/')}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model.apiKey}",
        },
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response_json = json.loads(response_body)
    return _extract_message_content(response_json), response_json.get("usage", {}).get("total_tokens"), elapsed_ms


def _extract_message_content(response_json: dict) -> str:
    choices = response_json.get("choices") or []
    if not choices:
        return json.dumps(response_json, ensure_ascii=False)

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(content or "").strip()
