import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from pypdf import PdfReader
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


DATA_DIR = BASE_DIR / "data"
PDFS_DIR = DATA_DIR / "raw" / "pdfs"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"


CONFIG_NAME = "meaning_count_domain_naming_on"
CONFIG = {"count": True, "domain": True, "naming": True}


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

TEST_MODE = False
TEST_FILE_COUNT = 1

RUN_NAME = f"{CONFIG_NAME}_test" if TEST_MODE else CONFIG_NAME
RAW_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
PROMPT_OUTPUT_DIR = OUTPUTS_DIR / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
SUMMARY_CSV = DATA_DIR / "annotations" / f"experiment_4_5_meaning_claude_sonnet_4_6_{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "术语数",
    "三元组数",
    "有效三元组数",
    "备注",
]


def build_client() -> OpenAI:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY":
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def get_domain_hint(domain: str) -> str:
    domain_path = PROMPTS_DIR / "modules" / f"domain_{domain.lower().strip()}.txt"
    if not domain_path.exists():
        raise FileNotFoundError(f"未找到领域提示文件: {domain_path}")
    return load_text(domain_path)


def get_module_text(enabled: bool, module_name: str) -> str:
    if not enabled:
        return ""

    module_path = PROMPTS_DIR / "modules" / module_name
    if not module_path.exists():
        raise FileNotFoundError(f"未找到提示模块文件: {module_path}")
    return load_text(module_path)


def build_prompt(domain: str, input_text: str) -> str:
    template_path = PROMPTS_DIR / "template" / "meaning_template.txt"
    template = load_text(template_path)

    domain_hint = get_domain_hint(domain) if CONFIG["domain"] else ""
    count_constraint = get_module_text(CONFIG["count"], "count_on.txt")
    naming_rules = get_module_text(CONFIG["naming"], "naming_on.txt")

    return (
        template
        .replace("{DOMAIN_HINT}", domain_hint)
        .replace("{COUNT_CONSTRAINT}", count_constraint)
        .replace("{NAMING_RULES}", naming_rules)
        .replace("{text}", input_text)
    )


def iter_input_files() -> list[tuple[str, str, Path]]:
    files: list[tuple[str, str, Path]] = []
    for path in sorted(PDFS_DIR.rglob("*.pdf")):
        files.append((path.parent.name.lower(), path.stem, path))

    if TEST_MODE:
        return files[:TEST_FILE_COUNT]
    return files


def clean_pdf_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines()]
    cleaned_lines: list[str] = []

    for line in lines:
        if not line:
            continue
        if line.startswith("%PDF-") or line in {"stream", "endstream", "endobj", "obj"}:
            continue
        if line.startswith("<<") or line.startswith(">>"):
            continue
        if line.startswith("/") or line.startswith("xref") or line.startswith("trailer"):
            continue
        if len(line) < 3:
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    text_parts: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_parts.append(page_text)

    cleaned_text = clean_pdf_text("\n".join(text_parts))
    if not cleaned_text:
        raise RuntimeError("未能从 PDF 中提取到可用文本。")
    return cleaned_text


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


def parse_result(raw_text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    result = json.loads(cleaned)

    terms = result.get("terms", [])
    triples = result.get("triples", [])

    if not isinstance(terms, list):
        raise ValueError("模型返回的 terms 字段不是列表。")
    if not isinstance(triples, list):
        raise ValueError("模型返回的 triples 字段不是列表。")

    result["terms"] = terms
    result["triples"] = triples
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
    return parse_result(raw_text), raw_text


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


def count_valid_triples(triples: list[dict[str, Any]]) -> int:
    required_keys = ("subject", "relation", "object")
    valid_count = 0
    for triple in triples:
        if all(str(triple.get(key, "")).strip() for key in required_keys):
            valid_count += 1
    return valid_count


def build_record(
    domain: str,
    doc_id: str,
    terms: list[Any],
    triples: list[dict[str, Any]],
    note: str = "",
) -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": RUN_NAME,
        "术语数": len(terms),
        "三元组数": len(triples),
        "有效三元组数": count_valid_triples(triples),
        "备注": note,
    }


def run() -> None:
    client = build_client()
    input_files = iter_input_files()
    if not input_files:
        raise FileNotFoundError(f"未在目录中找到 PDF 文件: {PDFS_DIR}")

    print(f"Found {len(input_files)} PDF files.")
    print(f"TEST_MODE={TEST_MODE}, RUN_NAME={RUN_NAME}")

    for domain, doc_id, input_path in tqdm(
        input_files,
        desc=f"{MODEL_OUTPUT_NAME} {RUN_NAME}",
        unit="pdf",
    ):
        print(f"Processing {domain}/{doc_id}")
        note = ""

        try:
            pdf_text = extract_pdf_text(input_path)
        except Exception as exc:
            result = {"terms": [], "triples": [], "error": str(exc)}
            save_json(result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
            append_csv(build_record(domain, doc_id, [], [], str(exc)), SUMMARY_CSV)
            time.sleep(SLEEP_SECONDS)
            continue

        prompt = build_prompt(domain, pdf_text)
        save_text(prompt, PROMPT_OUTPUT_DIR / domain / f"{doc_id}.txt")

        try:
            result, raw_text = call_llm(client, prompt)
            terms = result.get("terms", [])
            triples = result.get("triples", [])
            result.setdefault("_raw_text", raw_text)
        except Exception as exc:
            result = {"terms": [], "triples": [], "error": str(exc)}
            terms = []
            triples = []
            note = str(exc)

        save_json(result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        append_csv(build_record(domain, doc_id, terms, triples, note), SUMMARY_CSV)
        time.sleep(SLEEP_SECONDS)

    print("Done!")


if __name__ == "__main__":
    run()
