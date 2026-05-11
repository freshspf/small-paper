import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Union

from openai import OpenAI
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[4]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
ANNOTATION_OUTPUT_DIR = DATA_DIR / "annotations" / "experiment_4_5" / "claude_sonnet_4_6" / "transportation"


CONFIG_NAME = "baseline_chunk_json_transportation"


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
REQUEST_TIMEOUT_SECONDS = 600
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 5.0

INPUT_JSON_DIR = OUTPUTS_DIR / "preprocessed_inputs" / "experiment_4_5_pdf3" / "transportation"

RUN_NAME = CONFIG_NAME
RAW_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
PROMPT_OUTPUT_DIR = OUTPUTS_DIR / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
SUMMARY_CSV = ANNOTATION_OUTPUT_DIR / f"{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "分块数",
    "类数量",
    "属性数量",
    "subClassOf数量",
    "subPropertyOf数量",
    "domain数量",
    "range数量",
    "文档运行秒数",
    "累计运行秒数",
    "备注",
]

PROMPT_TEMPLATE = """You are an ontology construction system. Your task is to construct a conservative RDFS ontology directly from a single raw text chunk.

{domain_context}

CORE INSTRUCTIONS:

1. Work only on the current chunk.
   - Do not assume information from other chunks.
   - Do not merge with unseen context.

2. Extract ontology elements conservatively:
   - Classes: abstract concepts explicitly supported by the chunk.
   - Properties: relations explicitly supported by the chunk.

3. Keep the ontology minimal and high-confidence:
   - Use only terms and relations clearly grounded in the chunk.
   - Do not invent additional terms.
   - Do not perform ontology completion.
   - If evidence is weak, omit the axiom.

4. Construct hierarchy very strictly:
   - Infer rdfs:subClassOf only when the chunk explicitly states or very directly implies a subclass relation.
   - Infer rdfs:subPropertyOf only when the chunk clearly supports it.

5. Infer domain and range very strictly:
   - Only assign domain/range when the subject/object typing is explicit in the current chunk.
   - Do not guess missing domain/range.

6. Use consistent naming:
   - Classes in PascalCase.
   - Properties in camelCase.
   - Avoid vague names and unnecessary variants.

7. Output only what the current chunk supports.
   - Conservative extraction is preferred over completeness.

OUTPUT FORMAT:
Return a valid JSON object with the following structure:
{{
  "classes": [...],
  "properties": [...],
  "subClassOf": [
    {{"sub": "...", "super": "..."}}
  ],
  "subPropertyOf": [
    {{"sub": "...", "super": "..."}}
  ],
  "domain": [
    {{"property": "...", "class": "..."}}
  ],
  "range": [
    {{"property": "...", "class": "..."}}
  ]
}}

INPUT CHUNK METADATA:
- chunk_id: {chunk_id}
- section_title: {section_title}
- page_start: {page_start}
- page_end: {page_end}

INPUT TEXT CHUNK:
{text}
"""


def build_client() -> OpenAI:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY":
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def load_input_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"未找到输入 JSON 文件: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("输入 JSON 必须是 chunk 列表。")
    return data


def get_domain_context(domain: str) -> str:
    domain_key = domain.lower().strip()
    contexts = {
        "geography": (
            "**DOMAIN CONTEXT:**\n"
            "The input text belongs to the geography domain. Interpret ontology elements using geographic knowledge. "
            "Pay attention to spatial entities, locations, regions, environmental features, geographic structures, and spatial relationships."
        ),
        "medical": (
            "**DOMAIN CONTEXT:**\n"
            "The input text belongs to the medical domain. Interpret ontology elements using biomedical and clinical knowledge. "
            "Pay attention to diseases, symptoms, treatments, biological entities, patient-related concepts, and medical relations."
        ),
        "transportation": (
            "**DOMAIN CONTEXT:**\n"
            "The input text belongs to the transportation domain. Interpret ontology elements using transportation systems knowledge. "
            "Pay attention to vehicles, roads, traffic participants, infrastructure, mobility processes, and transport relations."
        ),
    }
    if domain_key not in contexts:
        raise ValueError(f"不支持的领域: {domain}")
    return contexts[domain_key]


def build_prompt(domain: str, chunk: dict[str, Any]) -> str:
    metadata = chunk.get("metadata", {})
    return PROMPT_TEMPLATE.format(
        domain_context=get_domain_context(domain),
        chunk_id=str(chunk.get("id", "")).strip(),
        section_title=str(metadata.get("section_title", "")).strip(),
        page_start=str(metadata.get("page_start", "")).strip(),
        page_end=str(metadata.get("page_end", "")).strip(),
        text=str(chunk.get("text", "")).strip(),
    )


def iter_input_files() -> list[tuple[str, str, Path]]:
    if not INPUT_JSON_DIR.exists():
        raise FileNotFoundError(f"未找到输入目录: {INPUT_JSON_DIR}")

    files: list[tuple[str, str, Path]] = []
    for path in sorted(INPUT_JSON_DIR.rglob("*.json")):
        files.append((path.parent.name.lower(), path.stem, path))
    return files


def extract_message_text(response: Any) -> str:
    if not response or not getattr(response, "choices", None):
        return ""

    message = response.choices[0].message
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
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


def normalize_string_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    normalized = []
    seen = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


def normalize_pair_list(items: Any, left_key: str, right_key: str) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        left = str(item.get(left_key, "")).strip()
        right = str(item.get(right_key, "")).strip()
        if not left or not right:
            continue
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({left_key: left, right_key: right})
    return normalized


def parse_result(raw_text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    if not cleaned:
        raise ValueError("Empty response body from model.")
    result = json.loads(cleaned)
    result["classes"] = normalize_string_list(result.get("classes", []))
    result["properties"] = normalize_string_list(result.get("properties", []))
    result["subClassOf"] = normalize_pair_list(result.get("subClassOf", []), "sub", "super")
    result["subPropertyOf"] = normalize_pair_list(result.get("subPropertyOf", []), "sub", "super")
    result["domain"] = normalize_pair_list(result.get("domain", []), "property", "class")
    result["range"] = normalize_pair_list(result.get("range", []), "property", "class")
    return result


def call_llm(client: OpenAI, prompt: str) -> tuple[dict[str, Any], str]:
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


def should_retry(exc: Exception) -> bool:
    message = str(exc).lower()
    retry_keywords = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "temporarily unavailable",
        "server error",
        "rate limit",
        "empty response",
        "empty response body",
        "expecting value",
        "unterminated string",
        "invalid control character",
        "invalid \\escape",
        "extra data",
    ]
    return any(keyword in message for keyword in retry_keywords)


def call_llm_with_retry(client: OpenAI, prompt: str, chunk_id: str) -> tuple[dict[str, Any], str]:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_llm(client, prompt)
        except Exception as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES or not should_retry(exc):
                raise
            print(f"Retrying chunk {chunk_id} ({attempt}/{MAX_RETRIES}) due to: {exc}")
            time.sleep(RETRY_DELAY_SECONDS)

    raise last_exc  # type: ignore[misc]


def save_json(data: Union[dict[str, Any], list[Any]], path: Path) -> None:
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


def merge_string_list(*lists: list[str]) -> list[str]:
    merged = []
    seen = set()
    for items in lists:
        for item in items:
            value = str(item).strip()
            if value and value not in seen:
                merged.append(value)
                seen.add(value)
    return merged


def merge_pair_list(items: list[dict[str, str]], left_key: str, right_key: str) -> list[dict[str, str]]:
    merged = []
    seen = set()
    for item in items:
        left = str(item.get(left_key, "")).strip()
        right = str(item.get(right_key, "")).strip()
        if not left or not right:
            continue
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        merged.append({left_key: left, right_key: right})
    return merged


def build_record(
    domain: str,
    doc_id: str,
    result: dict[str, Any],
    chunk_count: int,
    doc_elapsed_seconds: float,
    total_elapsed_seconds: float,
    note: str = "",
) -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": RUN_NAME,
        "分块数": chunk_count,
        "类数量": len(result.get("classes", [])),
        "属性数量": len(result.get("properties", [])),
        "subClassOf数量": len(result.get("subClassOf", [])),
        "subPropertyOf数量": len(result.get("subPropertyOf", [])),
        "domain数量": len(result.get("domain", [])),
        "range数量": len(result.get("range", [])),
        "文档运行秒数": f"{doc_elapsed_seconds:.2f}",
        "累计运行秒数": f"{total_elapsed_seconds:.2f}",
        "备注": note,
    }


def run() -> None:
    total_start_time = time.perf_counter()
    client = build_client()
    input_files = iter_input_files()
    if not input_files:
        raise ValueError(f"输入目录中没有 JSON 数据: {INPUT_JSON_DIR}")

    print(f"Found {len(input_files)} input JSON files.")
    print(f"RUN_NAME={RUN_NAME}")

    doc_chunks: list[tuple[str, str, Path, list[dict[str, Any]]]] = []
    total_chunks = 0
    for domain, doc_id, input_path in input_files:
        chunks = load_input_chunks(input_path)
        if not chunks:
            raise ValueError(f"输入 JSON 中没有 chunk 数据: {input_path}")
        doc_chunks.append((domain, doc_id, input_path, chunks))
        total_chunks += len(chunks)

    print(f"Total chunks to process: {total_chunks}")
    progress = tqdm(total=total_chunks, desc=f"{MODEL_OUTPUT_NAME} {RUN_NAME}", unit="chunk")

    for domain, doc_id, input_path, chunks in doc_chunks:
        print(f"Processing {domain}/{doc_id}")
        doc_start_time = time.perf_counter()

        chunk_results: list[dict[str, Any]] = []
        all_classes: list[str] = []
        all_properties: list[str] = []
        all_subclass: list[dict[str, str]] = []
        all_subproperty: list[dict[str, str]] = []
        all_domain: list[dict[str, str]] = []
        all_range: list[dict[str, str]] = []
        note_parts: list[str] = []

        for chunk in chunks:
            chunk_id = str(chunk.get("id", "")).strip() or "unknown_chunk"
            prompt = build_prompt(domain, chunk)
            save_text(prompt, PROMPT_OUTPUT_DIR / domain / doc_id / f"{chunk_id}.txt")

            raw_text = ""
            try:
                result, raw_text = call_llm_with_retry(client, prompt, chunk_id)
                result.setdefault("_raw_text", raw_text)
            except Exception as exc:
                result = {
                    "classes": [],
                    "properties": [],
                    "subClassOf": [],
                    "subPropertyOf": [],
                    "domain": [],
                    "range": [],
                    "error": str(exc),
                    "_raw_text": raw_text,
                }
                note_parts.append(f"{chunk_id}: {exc}")

            chunk_result = {
                "chunk_id": chunk_id,
                "metadata": chunk.get("metadata", {}),
                "classes": result.get("classes", []),
                "properties": result.get("properties", []),
                "subClassOf": result.get("subClassOf", []),
                "subPropertyOf": result.get("subPropertyOf", []),
                "domain": result.get("domain", []),
                "range": result.get("range", []),
                "error": result.get("error", ""),
                "_raw_text": result.get("_raw_text", ""),
            }
            chunk_results.append(chunk_result)
            save_json(chunk_result, RAW_OUTPUT_DIR / domain / doc_id / f"{chunk_id}.json")

            all_classes = merge_string_list(all_classes, result.get("classes", []))
            all_properties = merge_string_list(all_properties, result.get("properties", []))
            all_subclass.extend(result.get("subClassOf", []))
            all_subproperty.extend(result.get("subPropertyOf", []))
            all_domain.extend(result.get("domain", []))
            all_range.extend(result.get("range", []))
            progress.update(1)
            time.sleep(SLEEP_SECONDS)

        document_result = {
            "doc_id": doc_id,
            "domain": domain,
            "input_json": str(input_path),
            "chunk_count": len(chunks),
            "classes": all_classes,
            "properties": all_properties,
            "subClassOf": merge_pair_list(all_subclass, "sub", "super"),
            "subPropertyOf": merge_pair_list(all_subproperty, "sub", "super"),
            "domain_axioms": merge_pair_list(all_domain, "property", "class"),
            "range_axioms": merge_pair_list(all_range, "property", "class"),
            "chunk_results": chunk_results,
        }

        save_json(document_result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        doc_elapsed_seconds = time.perf_counter() - doc_start_time
        total_elapsed_seconds = time.perf_counter() - total_start_time
        print(
            f"Completed {domain}/{doc_id} in {doc_elapsed_seconds:.2f}s "
            f"(total elapsed: {total_elapsed_seconds:.2f}s)"
        )
        append_csv(
            build_record(
                domain,
                doc_id,
                {
                    "classes": document_result["classes"],
                    "properties": document_result["properties"],
                    "subClassOf": document_result["subClassOf"],
                    "subPropertyOf": document_result["subPropertyOf"],
                    "domain": document_result["domain_axioms"],
                    "range": document_result["range_axioms"],
                },
                len(chunks),
                doc_elapsed_seconds,
                total_elapsed_seconds,
                " | ".join(note_parts),
            ),
            SUMMARY_CSV,
        )
    progress.close()
    total_elapsed_seconds = time.perf_counter() - total_start_time
    print(f"Done! Total elapsed: {total_elapsed_seconds:.2f}s")


if __name__ == "__main__":
    run()
