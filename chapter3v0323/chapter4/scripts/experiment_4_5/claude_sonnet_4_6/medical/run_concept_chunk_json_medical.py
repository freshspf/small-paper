import csv
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Union

from openai import OpenAI
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[4]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
ANNOTATION_OUTPUT_DIR = DATA_DIR / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"


CONFIG_NAME = "concept_chunk_json"


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
GROUP_TRIPLE_SIZE = 30
GROUP_TERM_LIMIT = 120

INPUT_JSON_DIR = (
    OUTPUTS_DIR
    / "stage_inputs"
    / "experiment_4_5"
    / "claude_sonnet_4_6"
    / "concept_from_term_based_chunk_json"
    / "medical"
)

RUN_NAME = CONFIG_NAME
RAW_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
PROMPT_OUTPUT_DIR = OUTPUTS_DIR / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
SUMMARY_CSV = ANNOTATION_OUTPUT_DIR / f"{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "类数量",
    "属性数量",
    "subClassOf数量",
    "subPropertyOf数量",
    "domain数量",
    "range数量",
    "备注",
]

PROMPT_TEMPLATE = """You are an ontology construction system. Your task is to construct a formal RDFS ontology from normalized terms and semantic relations.

**DOMAIN CONTEXT:**
{domain_context}

CORE INSTRUCTIONS:

1. Identify ontology elements:
   - Classes: abstract concepts or conceptual categories
   - Properties: semantic relations suitable for ontology modeling

2. Use normalized terms from the input as your primary vocabulary.
   - Prefer using input normalized terms directly.
   - You may introduce a small number of additional high-confidence ontology elements only when they are strongly justified by the normalized terms and merged relations.
   - Do not introduce external background knowledge that is unsupported by the input.

3. Handle term types carefully:
   - Use terms labeled as Class as ontology classes.
   - Use terms labeled as Property as ontology properties.
   - Do not use Instance terms in rdfs:subClassOf relations.
   - Instance terms may help you infer domain/range, but should not be treated as classes unless strongly justified by the input.

4. Construct class hierarchy:
   - Infer rdfs:subClassOf when a subclass relation is explicit or strongly implied.
   - Moderate ontology completion is allowed if it is tightly grounded in the input and improves ontology coherence.
   - Avoid vague or overly general superclass invention.

5. Construct property hierarchy:
   - Infer rdfs:subPropertyOf only when clearly supported by the input.
   - If no reliable subproperty relation exists, return an empty list.

6. Infer domain and range:
   - For each ontology property, determine its domain and range conservatively.
   - Use normalized terms and merged evidence-bearing relations as the primary basis.
   - You may complete missing domain/range information when it is strongly implied by repeated evidence patterns.
   - Avoid speculative assignments.

7. Ensure ontology consistency:
   - Avoid duplication.
   - Prefer coherent and reusable ontology structures.
   - Keep results logically consistent.

**QUANTITY CONSTRAINT:**
Extract as many valid ontology axioms as possible. When the input strongly supports them, include multiple high-confidence classes, properties, hierarchies, domain axioms, and range axioms.

**ENTITY DEFINITIONS**

Class:
A general concept representing a category of entities, such as Disease, Patient, or Treatment.

Instance:
A specific entity belonging to a class, such as patient_JohnDoe or disease_COVID19.

Property:
A relation or attribute connecting classes or instances, such as hasSymptom, treatedBy, or locatedIn.

Please clearly distinguish between classes, instances, and properties when constructing ontology axioms.

**NAMING RULES**

Class Naming:
Use singular nouns or noun phrases in PascalCase (e.g., Person, Disease, MedicalProcedure). Avoid plural forms, special characters, or vague names.

Property Naming:
Use present-tense verbs or verb phrases in camelCase (e.g., hasSymptom, treatedBy, locatedIn). Use action-oriented names for relationships.

Instance Naming:
Use unique identifiers in lowercase or with underscores, optionally prefixed by class names. Avoid ambiguous names.

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

INPUT:
Normalized Terms:
{normalized_terms}

Merged Relations:
{updated_triples}
"""


def build_client() -> OpenAI:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY":
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def iter_input_files() -> list[Path]:
    if not INPUT_JSON_DIR.exists():
        raise FileNotFoundError(f"未找到输入目录: {INPUT_JSON_DIR}")

    files = sorted(INPUT_JSON_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"输入目录下没有 JSON 文件: {INPUT_JSON_DIR}")
    return files


def get_domain_context(domain: str) -> str:
    domain_map = {
        "geography": (
            "The input belongs to the geography domain. Interpret ontology elements using "
            "geographic knowledge. Pay attention to spatial entities, locations, regions, "
            "environmental features, geographic structures, and spatial relationships such "
            "as containment, adjacency, distribution, and location-based constraints."
        ),
        "medical": (
            "The input belongs to the medical domain. Interpret ontology elements using "
            "medical knowledge. Pay attention to diseases, symptoms, treatments, drugs, "
            "patients, clinical procedures, biomedical mechanisms, and healthcare relations "
            "such as diagnosis, treatment, causation, indication, and adverse effects."
        ),
        "transportation": (
            "The input belongs to the transportation domain. Interpret ontology elements "
            "using transportation knowledge. Pay attention to vehicles, infrastructure, "
            "traffic participants, routes, operations, logistics, networks, and relations "
            "such as movement, connection, scheduling, control, and service coverage."
        ),
    }
    return domain_map.get(
        domain.lower(),
        "The input belongs to a specialized academic domain. Interpret ontology elements "
        "using only the evidence provided in the input.",
    )


def load_input_result(path: Path) -> tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], Path]:
    if not path.exists():
        raise FileNotFoundError(f"未找到输入 JSON 文件: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    doc_id = str(data.get("doc_id", "")).strip() or path.stem
    domain = str(data.get("domain", "")).strip() or path.parent.name
    normalized_terms = data.get("normalized_terms", [])
    updated_triples = data.get("updated_triples", [])

    if not isinstance(normalized_terms, list):
        raise ValueError(f"输入文件中的 normalized_terms 字段不是列表: {path}")
    if not isinstance(updated_triples, list):
        raise ValueError(f"输入文件中的 updated_triples 字段不是列表: {path}")

    return doc_id, domain, normalized_terms, updated_triples, path


def simplify_normalized_terms(normalized_terms: list[dict[str, Any]]) -> list[dict[str, str]]:
    simplified = []
    seen: set[tuple[str, str]] = set()

    for item in normalized_terms:
        normalized = str(item.get("normalized", "")).strip()
        term_type = str(item.get("type", "")).strip()
        if not normalized or not term_type:
            continue
        key = (normalized, term_type)
        if key in seen:
            continue
        seen.add(key)
        simplified.append({"term": normalized, "type": term_type})

    return simplified


def simplify_updated_triples(updated_triples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    simplified = []
    seen: set[tuple[str, str, str]] = set()

    for triple in updated_triples:
        subject = str(triple.get("subject", "")).strip()
        relation = str(triple.get("relation", "")).strip()
        object_value = str(triple.get("object", "")).strip()
        if not subject or not relation or not object_value:
            continue

        key = (subject, relation, object_value)
        if key in seen:
            continue
        seen.add(key)
        simplified.append(
            {
                "subject": subject,
                "relation": relation,
                "object": object_value,
            }
        )

    return simplified


def build_prompt(domain: str, normalized_terms: list[dict[str, Any]], updated_triples: list[dict[str, Any]]) -> str:
    return PROMPT_TEMPLATE.format(
        domain_context=get_domain_context(domain),
        normalized_terms=json.dumps(simplify_normalized_terms(normalized_terms), ensure_ascii=False, indent=2),
        updated_triples=json.dumps(simplify_updated_triples(updated_triples), ensure_ascii=False, indent=2),
    )


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_grouped_inputs(
    normalized_terms: list[dict[str, Any]],
    updated_triples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized_term_pool: list[dict[str, str]] = simplify_normalized_terms(normalized_terms)
    term_map = {item["term"]: item["type"] for item in normalized_term_pool}
    groups: list[dict[str, Any]] = []
    used_terms: set[str] = set()

    for start in range(0, len(updated_triples), GROUP_TRIPLE_SIZE):
        triple_group = updated_triples[start : start + GROUP_TRIPLE_SIZE]
        referenced_terms = unique_preserve_order(
            [
                str(triple.get(key, "")).strip()
                for triple in triple_group
                for key in ("subject", "relation", "object")
                if str(triple.get(key, "")).strip()
            ]
        )

        group_terms: list[dict[str, str]] = []
        for term in referenced_terms:
            if term in term_map:
                group_terms.append({"term": term, "type": term_map[term]})

        if len(group_terms) < GROUP_TERM_LIMIT:
            for item in normalized_term_pool:
                if item["term"] in {term_item["term"] for term_item in group_terms}:
                    continue
                group_terms.append(item)
                if len(group_terms) >= GROUP_TERM_LIMIT:
                    break

        used_terms.update(item["term"] for item in group_terms)
        groups.append(
            {
                "group_index": len(groups) + 1,
                "normalized_terms": group_terms,
                "updated_triples": triple_group,
            }
        )

    remaining_terms = [item for item in normalized_term_pool if item["term"] not in used_terms]
    if remaining_terms:
        groups.append(
            {
                "group_index": len(groups) + 1,
                "normalized_terms": remaining_terms[:GROUP_TERM_LIMIT],
                "updated_triples": [],
            }
        )

    return groups


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
    retry_markers = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "rate limit",
        "server",
        "temporarily unavailable",
        "empty response body",
        "expecting value",
        "remoteprotocolerror",
        "apiconnectionerror",
        "readtimeout",
    ]
    return any(marker in message for marker in retry_markers)


def call_llm_with_retry(client: OpenAI, prompt: str, doc_id: str) -> tuple[dict[str, Any], str]:
    last_exc: Exception = Exception("Unknown model call failure.")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_llm(client, prompt)
        except Exception as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES or not should_retry(exc):
                break
            print(
                f"[Retry {attempt}/{MAX_RETRIES}] {doc_id} failed: {exc}. "
                f"Retrying in {RETRY_DELAY_SECONDS} seconds..."
            )
            time.sleep(RETRY_DELAY_SECONDS)

    raise last_exc


def merge_group_results(group_results: list[dict[str, Any]]) -> dict[str, Any]:
    merged = {
        "classes": [],
        "properties": [],
        "subClassOf": [],
        "subPropertyOf": [],
        "domain": [],
        "range": [],
    }

    string_fields = ["classes", "properties"]
    pair_fields = [
        ("subClassOf", "sub", "super"),
        ("subPropertyOf", "sub", "super"),
        ("domain", "property", "class"),
        ("range", "property", "class"),
    ]

    for field in string_fields:
        merged[field] = normalize_string_list(
            [
                item
                for result in group_results
                for item in result.get(field, [])
            ]
        )

    for field, left_key, right_key in pair_fields:
        merged[field] = normalize_pair_list(
            [
                item
                for result in group_results
                for item in result.get(field, [])
            ],
            left_key,
            right_key,
        )

    return merged


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


def build_record(domain: str, doc_id: str, result: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": RUN_NAME,
        "类数量": len(result.get("classes", [])),
        "属性数量": len(result.get("properties", [])),
        "subClassOf数量": len(result.get("subClassOf", [])),
        "subPropertyOf数量": len(result.get("subPropertyOf", [])),
        "domain数量": len(result.get("domain", [])),
        "range数量": len(result.get("range", [])),
        "备注": note,
    }


def run() -> None:
    client = build_client()
    input_files = iter_input_files()
    prepared_inputs: list[dict[str, Any]] = []
    total_groups = 0
    for path in input_files:
        doc_id, domain, normalized_terms, updated_triples, input_path = load_input_result(path)
        grouped_inputs = build_grouped_inputs(normalized_terms, updated_triples)
        prepared_inputs.append(
            {
                "doc_id": doc_id,
                "domain": domain,
                "normalized_terms": normalized_terms,
                "updated_triples": updated_triples,
                "input_path": input_path,
                "grouped_inputs": grouped_inputs,
            }
        )
        total_groups += len(grouped_inputs)

    print(f"Found {len(prepared_inputs)} input JSON files.")
    print(f"RUN_NAME={RUN_NAME}")
    print(f"Total group requests to run: {total_groups}")
    progress = tqdm(total=total_groups, desc=f"{MODEL_OUTPUT_NAME} {RUN_NAME}", unit="group")

    for item in prepared_inputs:
        doc_id = item["doc_id"]
        domain = item["domain"]
        normalized_terms = item["normalized_terms"]
        updated_triples = item["updated_triples"]
        input_path = item["input_path"]
        grouped_inputs = item["grouped_inputs"]
        print(f"Processing {domain}/{doc_id}")
        note = ""
        group_prompt_dir = PROMPT_OUTPUT_DIR / domain / doc_id
        raw_group_outputs: list[dict[str, Any]] = []
        group_results: list[dict[str, Any]] = []

        try:
            for group in grouped_inputs:
                group_index = int(group["group_index"])
                print(f"  Group {group_index}/{len(grouped_inputs)}")
                prompt = build_prompt(domain, group["normalized_terms"], group["updated_triples"])
                save_text(prompt, group_prompt_dir / f"group_{group_index:02d}.txt")

                group_result, group_raw_text = call_llm_with_retry(
                    client,
                    prompt,
                    f"{doc_id}/group_{group_index:02d}",
                )
                group_results.append(group_result)
                raw_group_outputs.append(
                    {
                        "group_index": group_index,
                        "normalized_terms": group["normalized_terms"],
                        "updated_triples": group["updated_triples"],
                        "result": group_result,
                        "_raw_text": group_raw_text,
                    }
                )
                progress.update(1)

            result = merge_group_results(group_results)
        except Exception as exc:
            result = {
                "classes": [],
                "properties": [],
                "subClassOf": [],
                "subPropertyOf": [],
                "domain": [],
                "range": [],
                "error": str(exc),
                "_input_result_file": str(input_path),
            }
            raw_group_outputs.append({"group_index": -1, "error": str(exc)})
            note = str(exc)

        output_result = {
            "doc_id": doc_id,
            "domain": domain,
            "input_json": str(input_path),
            "group_triple_size": GROUP_TRIPLE_SIZE,
            "group_term_limit": GROUP_TERM_LIMIT,
            "group_count": len(grouped_inputs),
            "group_results": raw_group_outputs,
            "classes": result.get("classes", []),
            "properties": result.get("properties", []),
            "subClassOf": result.get("subClassOf", []),
            "subPropertyOf": result.get("subPropertyOf", []),
            "domain_axioms": result.get("domain", []),
            "range_axioms": result.get("range", []),
            "error": result.get("error", ""),
        }

        save_json(output_result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        append_csv(build_record(domain, doc_id, result, note), SUMMARY_CSV)
        time.sleep(SLEEP_SECONDS)
    progress.close()
    print("Done!")


if __name__ == "__main__":
    run()
