import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.common.prompt_builder import build_prompt


DATA_DIR = BASE_DIR / "data"
ABSTRACTS_DIR = DATA_DIR / "raw" / "abstracts"
OUTPUTS_DIR = BASE_DIR / "outputs"


CONFIG_NAME = "baseline"
CONFIG = {"count": False, "domain": False, "naming": False, "entity": False}


# ======================
# 手动配置区
# ======================
MODEL_NAME = "claude-sonnet-4-6"
MODEL_OUTPUT_NAME = "Claude-Sonnet-4.6"
OPENAI_API_KEY = "sk-dusmrPQZswbeAR4EejXA67BozRsyvREZs9myIINYgVaKiEnI"
OPENAI_BASE_URL = "https://api2.aigcbest.top/v1"

MAX_TOKENS = 8192
TEMPERATURE = 0.0
SLEEP_SECONDS = 0.5

RAW_OUTPUT_DIR = (
    OUTPUTS_DIR / "raw_outputs" / "count_constraint_ablation" / "claude_sonnet_4.6" / CONFIG_NAME
)
PROMPT_OUTPUT_DIR = (
    OUTPUTS_DIR / "prompts" / "count_constraint_ablation" / "claude_sonnet_4.6" / CONFIG_NAME
)
SUMMARY_CSV = DATA_DIR / "annotations" / "count_constraint_ablation_claude_sonnet_4_6_baseline.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "抽取术语数",
    "抽取公理数",
    "正确公理数",
    "公理正确率",
    "有效公理数",
    "类型正确数",
    "类型准确率",
    "术语规范性",
    "备注",
]


def build_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def iter_input_files() -> list[tuple[str, str, Path]]:
    files: list[tuple[str, str, Path]] = []
    for path in sorted(ABSTRACTS_DIR.rglob("*.txt")):
        files.append((path.parent.name, path.stem, path))
    return files


def extract_message_text(response: Any) -> str:
    if not response or not getattr(response, "choices", None):
        return ""

    message = response.choices[0].message
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    text_parts.append(str(text_value))
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    text_parts.append(str(text_value))
        return "\n".join(text_parts).strip()

    return str(content or "").strip()


def strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def parse_axiom_result(raw_text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    result = json.loads(cleaned)
    axioms = result.get("axioms", [])
    if not isinstance(axioms, list):
        raise ValueError("模型返回的 axioms 字段不是列表。")
    result["axioms"] = axioms
    return result


def call_llm(client: OpenAI, prompt: str) -> tuple[dict[str, Any], str]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = extract_message_text(response)
    return parse_axiom_result(raw_text), raw_text


def save_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_csv(record: dict[str, Any], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists or csv_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(record)


def count_terms(axioms: list[dict[str, Any]]) -> int:
    terms: set[str] = set()
    for axiom in axioms:
        for key in ("subject", "object"):
            value = str(axiom.get(key, "")).strip()
            if value:
                terms.add(value)
    return len(terms)


def count_valid_axioms(axioms: list[dict[str, Any]]) -> int:
    required_keys = ("subject", "relation", "object", "evidence")
    valid_count = 0
    for axiom in axioms:
        if all(str(axiom.get(key, "")).strip() for key in required_keys):
            valid_count += 1
    return valid_count


def build_record(domain: str, doc_id: str, axioms: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": CONFIG_NAME,
        "抽取术语数": count_terms(axioms),
        "抽取公理数": len(axioms),
        "正确公理数": "",
        "公理正确率": "",
        "有效公理数": count_valid_axioms(axioms),
        "类型正确数": "",
        "类型准确率": "",
        "术语规范性": "",
        "备注": note,
    }


def run() -> None:
    client = build_client()
    input_files = iter_input_files()
    if not input_files:
        raise FileNotFoundError(f"未在目录中找到摘要文件: {ABSTRACTS_DIR}")

    print(f"Found {len(input_files)} abstract files.")

    for domain, doc_id, input_path in tqdm(
        input_files,
        desc=f"{MODEL_OUTPUT_NAME} {CONFIG_NAME}",
        unit="doc",
    ):
        text = input_path.read_text(encoding="utf-8")
        print(f"Processing {domain}/{doc_id}")

        prompt = build_prompt(CONFIG, domain, text)
        note = ""
        save_text(prompt, PROMPT_OUTPUT_DIR / domain / f"{doc_id}.txt")

        try:
            result, raw_text = call_llm(client, prompt)
            axioms = result.get("axioms", [])
            result.setdefault("_raw_text", raw_text)
        except Exception as exc:
            result = {"axioms": [], "error": str(exc)}
            axioms = []
            note = str(exc)

        save_json(result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        append_csv(build_record(domain, doc_id, axioms, note), SUMMARY_CSV)
        time.sleep(SLEEP_SECONDS)

    print("Done!")


if __name__ == "__main__":
    run()
