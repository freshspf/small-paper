import csv
import json
import re
import sys
import time
from math import ceil
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"


CONFIG_NAME = "term_domain_naming_entity_on_chunked"
CONFIG = {"domain": True, "naming": True, "entity": True}


# ======================
# 手动配置区
# ======================
MODEL_NAME = "gpt-5.4"
MODEL_OUTPUT_NAME = "GPT-5.4"
OPENAI_API_KEY = "sk-dusmrPQZswbeAR4EejXA67BozRsyvREZs9myIINYgVaKiEnI"
OPENAI_BASE_URL = "https://api2.aigcbest.top/v1"

INPUT_RESULT_DIR = (
    OUTPUTS_DIR
    / "raw_outputs"
    / "experiment_4_5"
    / "gpt_5_4"
    / "meaning_count_domain_naming_on"
)

MAX_TOKENS = 8192
TEMPERATURE = 0.0
SLEEP_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 600
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 5.0

TERM_CHUNK_SIZE = 40
TRIPLE_CHUNK_SIZE = 40

TEST_MODE = False
TEST_FILE_COUNT = 1

RUN_NAME = f"{CONFIG_NAME}_test" if TEST_MODE else CONFIG_NAME
RAW_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "gpt_5_4" / RUN_NAME
PROMPT_OUTPUT_DIR = OUTPUTS_DIR / "prompts" / "experiment_4_5" / "gpt_5_4" / RUN_NAME
SUMMARY_CSV = DATA_DIR / "annotations" / f"experiment_4_5_term_gpt_5_4_{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "标准化术语数",
    "更新后三元组数",
    "有效更新后三元组数",
    "分块数",
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


def build_prompt(domain: str, terms: list[Any], triples: list[dict[str, Any]]) -> str:
    template_path = PROMPTS_DIR / "template" / "term_template.txt"
    template = load_text(template_path)

    domain_hint = get_domain_hint(domain) if CONFIG["domain"] else ""
    entity_definition = get_module_text(CONFIG["entity"], "entity_on.txt")
    naming_rules = get_module_text(CONFIG["naming"], "naming_on.txt")

    terms_text = json.dumps(terms, ensure_ascii=False, separators=(",", ":"))
    triples_text = json.dumps(triples, ensure_ascii=False, separators=(",", ":"))

    return (
        template
        .replace("{DOMAIN_HINT}", domain_hint)
        .replace("{ENTITY_DEFINITION}", entity_definition)
        .replace("{NAMING_RULES}", naming_rules)
        .replace("{terms}", terms_text)
        .replace("{triples}", triples_text)
    )


def iter_input_files() -> list[tuple[str, str, Path]]:
    files: list[tuple[str, str, Path]] = []
    for path in sorted(INPUT_RESULT_DIR.rglob("*.json")):
        files.append((path.parent.name.lower(), path.stem, path))

    if TEST_MODE:
        return files[:TEST_FILE_COUNT]
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


def parse_result(raw_text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    if not cleaned:
        raise ValueError("Empty response body from model.")

    result = json.loads(cleaned)
    normalized_terms = result.get("normalized_terms", [])
    updated_triples = result.get("updated_triples", [])

    if not isinstance(normalized_terms, list):
        raise ValueError("模型返回的 normalized_terms 字段不是列表。")
    if not isinstance(updated_triples, list):
        raise ValueError("模型返回的 updated_triples 字段不是列表。")

    result["normalized_terms"] = normalized_terms
    result["updated_triples"] = updated_triples
    return result


def is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retryable_keywords = [
        "timed out",
        "timeout",
        "connection",
        "network",
        "temporarily unavailable",
        "server disconnected",
        "connection reset",
        "remoteprotocolerror",
        "readerror",
        "api connection",
        "empty response",
        "expecting value",
        "502",
        "503",
        "504",
    ]
    return any(keyword in message for keyword in retryable_keywords)


def call_llm(client: OpenAI, prompt: str) -> tuple[dict[str, Any], str]:
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            raw_text = extract_message_text(response)
            return parse_result(raw_text), raw_text
        except Exception as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES or not is_retryable_error(exc):
                raise

            wait_seconds = RETRY_DELAY_SECONDS * attempt
            print(
                f"[Retry {attempt}/{MAX_RETRIES}] {type(exc).__name__}: {exc}. "
                f"Waiting {wait_seconds:.1f}s before retry."
            )
            time.sleep(wait_seconds)

    raise RuntimeError(str(last_exc) if last_exc else "模型调用失败。")


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


def load_meaning_result(path: Path) -> tuple[list[Any], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    terms = data.get("terms", [])
    triples = data.get("triples", [])

    if not isinstance(terms, list):
        raise ValueError(f"输入文件中的 terms 字段不是列表: {path}")
    if not isinstance(triples, list):
        raise ValueError(f"输入文件中的 triples 字段不是列表: {path}")

    return terms, triples


def dedupe_terms(terms: list[Any]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for term in terms:
        value = str(term).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    return deduped


def dedupe_triples(triples: list[dict[str, Any]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for triple in triples:
        subject = str(triple.get("subject", "")).strip()
        relation = str(triple.get("relation", "")).strip()
        object_value = str(triple.get("object", "")).strip()
        if not subject or not relation or not object_value:
            continue

        key = (subject, relation, object_value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"subject": subject, "relation": relation, "object": object_value})

    return deduped


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    if not items:
        return [[]]
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def build_chunks(terms: list[Any], triples: list[dict[str, Any]]) -> list[tuple[list[str], list[dict[str, str]]]]:
    term_chunks = chunk_list(dedupe_terms(terms), TERM_CHUNK_SIZE)
    triple_chunks = chunk_list(dedupe_triples(triples), TRIPLE_CHUNK_SIZE)
    chunk_count = max(len(term_chunks), len(triple_chunks))

    chunks: list[tuple[list[str], list[dict[str, str]]]] = []
    for idx in range(chunk_count):
        term_chunk = term_chunks[idx] if idx < len(term_chunks) else []
        triple_chunk = triple_chunks[idx] if idx < len(triple_chunks) else []
        chunks.append((term_chunk, triple_chunk))
    return chunks


def merge_normalized_terms(chunk_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for result in chunk_results:
        for item in result.get("normalized_terms", []):
            original = str(item.get("original", "")).strip()
            normalized = str(item.get("normalized", "")).strip()
            term_type = str(item.get("type", "")).strip()
            if not original or not normalized or not term_type:
                continue

            key = (original, normalized, term_type)
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "original": original,
                    "normalized": normalized,
                    "type": term_type,
                }
            )

    return merged


def merge_updated_triples(chunk_results: list[dict[str, Any]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for result in chunk_results:
        for triple in result.get("updated_triples", []):
            subject = str(triple.get("subject", "")).strip()
            relation = str(triple.get("relation", "")).strip()
            object_value = str(triple.get("object", "")).strip()
            if not subject or not relation or not object_value:
                continue

            key = (subject, relation, object_value)
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "subject": subject,
                    "relation": relation,
                    "object": object_value,
                }
            )

    return merged


def has_successful_output(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    if data.get("error"):
        return False

    normalized_terms = data.get("normalized_terms", [])
    updated_triples = data.get("updated_triples", [])
    return isinstance(normalized_terms, list) and isinstance(updated_triples, list)


def build_record(
    domain: str,
    doc_id: str,
    normalized_terms: list[dict[str, Any]],
    updated_triples: list[dict[str, Any]],
    chunk_count: int,
    note: str = "",
) -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": RUN_NAME,
        "标准化术语数": len(normalized_terms),
        "更新后三元组数": len(updated_triples),
        "有效更新后三元组数": count_valid_triples(updated_triples),
        "分块数": chunk_count,
        "备注": note,
    }


def run() -> None:
    client = build_client()
    input_files = iter_input_files()
    if not input_files:
        raise FileNotFoundError(f"未在目录中找到 meaning 层输出文件: {INPUT_RESULT_DIR}")

    print(f"Found {len(input_files)} meaning result files.")
    print(f"TEST_MODE={TEST_MODE}, RUN_NAME={RUN_NAME}")

    for domain, doc_id, input_path in tqdm(
        input_files,
        desc=f"{MODEL_OUTPUT_NAME} {RUN_NAME}",
        unit="doc",
    ):
        print(f"Processing {domain}/{doc_id}")
        output_path = RAW_OUTPUT_DIR / domain / f"{doc_id}.json"
        if has_successful_output(output_path):
            print(f"Skipping {domain}/{doc_id} because a successful output already exists.")
            continue

        note = ""

        try:
            terms, triples = load_meaning_result(input_path)
            chunks = build_chunks(terms, triples)
        except Exception as exc:
            result = {"normalized_terms": [], "updated_triples": [], "error": str(exc)}
            save_json(result, output_path)
            append_csv(build_record(domain, doc_id, [], [], 0, str(exc)), SUMMARY_CSV)
            time.sleep(SLEEP_SECONDS)
            continue

        chunk_results: list[dict[str, Any]] = []
        failed_chunks: list[dict[str, Any]] = []

        for idx, (term_chunk, triple_chunk) in enumerate(chunks, start=1):
            prompt = build_prompt(domain, term_chunk, triple_chunk)
            save_text(prompt, PROMPT_OUTPUT_DIR / domain / doc_id / f"chunk_{idx:03d}.txt")

            try:
                result, raw_text = call_llm(client, prompt)
                result.setdefault("_raw_text", raw_text)
                result.setdefault("_chunk_index", idx)
                result.setdefault("_input_result_file", str(input_path))
                chunk_results.append(result)
                save_json(result, RAW_OUTPUT_DIR / domain / doc_id / f"chunk_{idx:03d}.json")
            except Exception as exc:
                chunk_error = {
                    "normalized_terms": [],
                    "updated_triples": [],
                    "error": str(exc),
                    "_chunk_index": idx,
                    "_input_result_file": str(input_path),
                }
                failed_chunks.append(chunk_error)
                save_json(chunk_error, RAW_OUTPUT_DIR / domain / doc_id / f"chunk_{idx:03d}.json")

        if failed_chunks:
            note = f"{len(failed_chunks)}/{len(chunks)} chunk(s) failed"

        merged_result = {
            "normalized_terms": merge_normalized_terms(chunk_results),
            "updated_triples": merge_updated_triples(chunk_results),
            "_input_result_file": str(input_path),
            "_chunk_count": len(chunks),
            "_successful_chunk_count": len(chunk_results),
            "_failed_chunk_count": len(failed_chunks),
        }
        if failed_chunks:
            merged_result["error"] = note

        save_json(merged_result, output_path)
        append_csv(
            build_record(
                domain,
                doc_id,
                merged_result["normalized_terms"],
                merged_result["updated_triples"],
                len(chunks),
                note,
            ),
            SUMMARY_CSV,
        )
        time.sleep(SLEEP_SECONDS)

    print("Done!")


if __name__ == "__main__":
    run()
