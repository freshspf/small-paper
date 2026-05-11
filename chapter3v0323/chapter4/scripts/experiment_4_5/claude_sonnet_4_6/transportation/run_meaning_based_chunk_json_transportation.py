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


CONFIG_NAME = "meaning_based_chunk_json_transportation"


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
TERM_INPUT_DIR = OUTPUTS_DIR / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_from_meaning_based_chunk_json"
SUMMARY_CSV = ANNOTATION_OUTPUT_DIR / f"{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "分块数",
    "术语数",
    "五元组数",
    "有效五元组数",
    "文档运行秒数",
    "累计运行秒数",
    "备注",
]

PROMPT_TEMPLATE = """You are an ontology axiom extraction system. Your task is to identify key concepts and relationships from the given scientific or technical text chunk.

{domain_context}

**CORE INSTRUCTIONS:**
1. Identify important terms (concepts, entities, and relations) in the text chunk.
2. Extract semantic relationships from the text chunk in the form of five-field records.
3. Focus on capturing information explicitly stated in the text chunk.
4. Avoid high-level abstraction such as ontology hierarchy construction.
5. Each extracted relation must preserve its source chunk id and the exact sentence or sentence span used as evidence.
6. The "chunk" field must be exactly the provided chunk id.
7. The "context" field must be the exact sentence or minimal sentence span from this chunk that supports the extracted relation. Do not summarize or paraphrase the evidence.

**QUANTITY CONSTRAINT:**
Extract as many valid ontology axioms as possible. For each axiom type, try to construct multiple candidate axioms whenever the text provides sufficient information.

**NAMING RULES**

Class Naming:
Use singular nouns or noun phrases in PascalCase (e.g., Person, Disease, MedicalProcedure). Avoid plural forms, special characters, or vague names.

Property Naming:
Use present-tense verbs or verb phrases in camelCase (e.g., hasSymptom, treatedBy, locatedIn). Use action-oriented names for relationships.

Instance Naming:
Use unique identifiers in lowercase or with underscores, optionally prefixed by class names (e.g., patient_JohnDoe, disease_COVID19). Avoid ambiguous names.

**OUTPUT FORMAT:**
Return a valid JSON object with the following structure:
{{
  "terms": ["..."],
  "triples": [
    {{
      "subject": "...",
      "relation": "...",
      "object": "...",
      "chunk": "{chunk_id}",
      "context": "exact supporting sentence from this chunk"
    }}
  ]
}}

**INPUT CHUNK METADATA:**
- chunk_id: {chunk_id}
- section_title: {section_title}
- page_start: {page_start}
- page_end: {page_end}

**INPUT TEXT CHUNK:**
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
            "The input text belongs to the geography domain. Please interpret terms, relationships, and constraints using geographic knowledge. "
            "Pay attention to spatial entities, locations, regions, environmental features, and geographic relationships such as containment, adjacency, and spatial distribution."
        ),
        "medical": (
            "**DOMAIN CONTEXT:**\n"
            "The input text belongs to the medical domain. Please interpret terms, relationships, and constraints using biomedical and clinical knowledge. "
            "Pay attention to diseases, symptoms, treatments, biological entities, patient-related concepts, and medical causal or associative relations."
        ),
        "transportation": (
            "**DOMAIN CONTEXT:**\n"
            "The input text belongs to the transportation domain. Please interpret terms, relationships, and constraints using transportation systems knowledge. "
            "Pay attention to vehicles, roads, traffic participants, mobility processes, transport infrastructure, and operational or spatiotemporal transportation relations."
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


def normalize_terms(terms: Any) -> list[str]:
    if not isinstance(terms, list):
        raise ValueError("模型返回的 terms 字段不是列表。")
    normalized: list[str] = []
    seen: set[str] = set()
    for term in terms:
        term_text = str(term).strip()
        if term_text and term_text not in seen:
            normalized.append(term_text)
            seen.add(term_text)
    return normalized


def normalize_triples(triples: Any, chunk_id: str) -> list[dict[str, Any]]:
    if not isinstance(triples, list):
        raise ValueError("模型返回的 triples 字段不是列表。")

    normalized: list[dict[str, Any]] = []
    for item in triples:
        if not isinstance(item, dict):
            continue
        triple = {
            "subject": str(item.get("subject", "")).strip(),
            "relation": str(item.get("relation", "")).strip(),
            "object": str(item.get("object", "")).strip(),
            "chunk": str(item.get("chunk", "")).strip() or chunk_id,
            "context": str(item.get("context", "")).strip(),
        }
        normalized.append(triple)
    return normalized


def parse_result(raw_text: str, chunk_id: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    if not cleaned:
        raise ValueError("Empty response body from model.")
    result = json.loads(cleaned)
    terms = normalize_terms(result.get("terms", []))
    triples = normalize_triples(result.get("triples", []), chunk_id)
    result["terms"] = terms
    result["triples"] = triples
    return result


def call_llm(client: OpenAI, prompt: str, chunk_id: str) -> tuple[dict[str, Any], str]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    raw_text = extract_message_text(response)
    return parse_result(raw_text, chunk_id), raw_text


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
            return call_llm(client, prompt, chunk_id)
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


def count_valid_triples(triples: list[dict[str, Any]]) -> int:
    required_keys = ("subject", "relation", "object", "chunk", "context")
    valid_count = 0
    for triple in triples:
        if all(str(triple.get(key, "")).strip() for key in required_keys):
            valid_count += 1
    return valid_count


def build_record(
    domain: str,
    doc_id: str,
    chunk_count: int,
    terms: list[str],
    triples: list[dict[str, Any]],
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
        "术语数": len(terms),
        "五元组数": len(triples),
        "有效五元组数": count_valid_triples(triples),
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

        all_terms: list[str] = []
        all_triples: list[dict[str, Any]] = []
        chunk_results: list[dict[str, Any]] = []
        note_parts: list[str] = []

        for chunk in chunks:
            chunk_id = str(chunk.get("id", "")).strip() or "unknown_chunk"
            prompt = build_prompt(domain, chunk)
            save_text(prompt, PROMPT_OUTPUT_DIR / domain / doc_id / f"{chunk_id}.txt")

            raw_text = ""
            try:
                result, raw_text = call_llm_with_retry(client, prompt, chunk_id)
                terms = result.get("terms", [])
                triples = result.get("triples", [])
                result.setdefault("_raw_text", raw_text)
            except Exception as exc:
                result = {
                    "terms": [],
                    "triples": [],
                    "error": str(exc),
                    "_raw_text": raw_text,
                    "_chunk_id": chunk_id,
                }
                terms = []
                triples = []
                note_parts.append(f"{chunk_id}: {exc}")

            chunk_result = {
                "chunk_id": chunk_id,
                "metadata": chunk.get("metadata", {}),
                "terms": terms,
                "triples": triples,
                "error": result.get("error", ""),
                "_raw_text": result.get("_raw_text", ""),
            }
            chunk_results.append(chunk_result)

            all_terms.extend(terms)
            all_triples.extend(triples)
            save_json(chunk_result, RAW_OUTPUT_DIR / domain / doc_id / f"{chunk_id}.json")
            progress.update(1)
            time.sleep(SLEEP_SECONDS)

        aggregated_terms = [term for term in all_terms if str(term).strip()]
        aggregated_triples = all_triples

        document_result = {
            "doc_id": doc_id,
            "domain": domain,
            "input_json": str(input_path),
            "chunk_count": len(chunks),
            "terms": aggregated_terms,
            "triples": aggregated_triples,
            "chunk_results": chunk_results,
        }

        term_input_result = {
            "doc_id": doc_id,
            "domain": domain,
            "source_run": RUN_NAME,
            "source_json": str(RAW_OUTPUT_DIR / domain / f"{doc_id}.json"),
            "chunk_count": len(chunks),
            "terms": aggregated_terms,
            "triples": aggregated_triples,
        }

        save_json(document_result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        save_json(term_input_result, TERM_INPUT_DIR / domain / f"{doc_id}.json")
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
                len(chunks),
                aggregated_terms,
                aggregated_triples,
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
