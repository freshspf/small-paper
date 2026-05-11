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
ANNOTATION_OUTPUT_DIR = DATA_DIR / "annotations" / "experiment_4_5" / "claude_sonnet_4_6" / "geography"


CONFIG_NAME = "term_based_chunk_json_geography"


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
GROUP_TRIPLE_SIZE = 25
GROUP_TERM_LIMIT = 80

INPUT_JSON_DIR = (
    OUTPUTS_DIR
    / "stage_inputs"
    / "experiment_4_5"
    / "claude_sonnet_4_6"
    / "term_from_meaning_based_chunk_json"
    / "geography"
)

RUN_NAME = CONFIG_NAME
RAW_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
PROMPT_OUTPUT_DIR = OUTPUTS_DIR / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / RUN_NAME
CONCEPT_INPUT_DIR = OUTPUTS_DIR / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_from_term_based_chunk_json"
SUMMARY_CSV = ANNOTATION_OUTPUT_DIR / f"{RUN_NAME}.csv"

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "标准化术语数",
    "归并后关系数",
    "有效归并后关系数",
    "备注",
]

PROMPT_TEMPLATE = """You are an ontology normalization system. Your task is to refine and normalize extracted terms for ontology construction.

{domain_context}

CORE INSTRUCTIONS:

1. Normalize terms:
   - Merge synonymous or equivalent terms into a unified representation.
   - Remove redundant or overly specific variants if they represent the same concept.
   - Ensure consistent naming style across all terms.

2. Assign semantic types to each term:
   Use a task-oriented typing strategy:

   - Class: abstract concepts, categories, or conceptual structures
   - Instance: specific systems, datasets, tools, or named entities
   - Property: relationships, actions, or operations between concepts

   When uncertain:
   - Prefer Class for conceptual entities
   - Prefer Instance for named systems, tools, or datasets
   - Prefer Property for verbs or relation-like terms

3. Resolve ambiguities:
   - Ensure each term has a clear and consistent semantic role
   - Avoid assigning multiple types to the same term

4. Enforce naming rules:
   - Use concise noun or noun phrases
   - Use a consistent naming style
   - Remove unnecessary prefixes if they do not add ontology value
   - Avoid generic words such as "concept", "object", "thing"

5. Focus only on term normalization:
   - Do not output merged relations.
   - Do not rewrite or remove triples directly.
   - Your job is to provide a reliable normalization mapping that can later be applied deterministically by code.

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
Use unique identifiers in lowercase or with underscores, optionally prefixed by class names (e.g., patient_JohnDoe, disease_COVID19). Avoid ambiguous names.

OUTPUT FORMAT:
Return a valid JSON object with the following structure:

{{
  "normalized_terms": [
    {{
      "original": "...",
      "normalized": "...",
      "type": "Class | Instance | Property"
    }}
  ]
}}

INPUT:

Terms:
{terms}

Triples:
{triples}
"""


def build_client() -> OpenAI:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY":
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def load_input_result(path: Path) -> tuple[str, str, list[Any], list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"未找到输入 JSON 文件: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    doc_id = str(data.get("doc_id", "")).strip() or path.stem
    domain = str(data.get("domain", "")).strip() or path.parent.name
    terms = data.get("terms", [])
    triples = data.get("triples", [])

    if not isinstance(terms, list):
        raise ValueError(f"输入文件中的 terms 字段不是列表: {path}")
    if not isinstance(triples, list):
        raise ValueError(f"输入文件中的 triples 字段不是列表: {path}")

    return doc_id, domain, terms, triples


def get_input_chunk_count(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    chunk_count = data.get("chunk_count", 0)
    try:
        return int(chunk_count)
    except Exception:
        return 0


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


def iter_input_files() -> list[Path]:
    if not INPUT_JSON_DIR.exists():
        raise FileNotFoundError(f"未找到输入目录: {INPUT_JSON_DIR}")
    return sorted(INPUT_JSON_DIR.glob("*.json"))


def build_prompt(domain: str, terms: list[Any], triples: list[dict[str, Any]]) -> str:
    return PROMPT_TEMPLATE.format(
        domain_context=get_domain_context(domain),
        terms=json.dumps(terms, ensure_ascii=False, indent=2),
        triples=json.dumps(triples, ensure_ascii=False, indent=2),
    )


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_grouped_inputs(terms: list[Any], triples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_terms = unique_preserve_order([str(term).strip() for term in terms if str(term).strip()])
    groups: list[dict[str, Any]] = []
    used_terms: set[str] = set()

    for start in range(0, len(triples), GROUP_TRIPLE_SIZE):
        triple_group = triples[start : start + GROUP_TRIPLE_SIZE]
        group_terms: list[str] = []

        for triple in triple_group:
            for key in ("subject", "relation", "object"):
                value = str(triple.get(key, "")).strip()
                if value:
                    group_terms.append(value)

        merged_terms = unique_preserve_order(group_terms)
        if len(merged_terms) < GROUP_TERM_LIMIT:
            for term in cleaned_terms:
                if term in merged_terms:
                    continue
                merged_terms.append(term)
                if len(merged_terms) >= GROUP_TERM_LIMIT:
                    break

        used_terms.update(merged_terms)
        groups.append(
            {
                "group_index": len(groups) + 1,
                "terms": merged_terms,
                "triples": triple_group,
            }
        )

    remaining_terms = [term for term in cleaned_terms if term not in used_terms]
    if remaining_terms:
        groups.append(
            {
                "group_index": len(groups) + 1,
                "terms": remaining_terms[:GROUP_TERM_LIMIT],
                "triples": [],
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


def normalize_mapping_items(items: Any) -> list[dict[str, str]]:
    if not isinstance(items, list):
        raise ValueError("模型返回的 normalized_terms 字段不是列表。")

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "original": str(item.get("original", "")).strip(),
                "normalized": str(item.get("normalized", "")).strip(),
                "type": str(item.get("type", "")).strip(),
            }
        )
    return normalized


def parse_result(raw_text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw_text)
    if not cleaned:
        raise ValueError("Empty response body from model.")
    result = json.loads(cleaned)

    normalized_terms = normalize_mapping_items(result.get("normalized_terms", []))
    result["normalized_terms"] = normalized_terms
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


def call_llm_with_retry(client: OpenAI, prompt: str, doc_id: str) -> tuple[dict[str, Any], str]:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_llm(client, prompt)
        except Exception as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES or not should_retry(exc):
                raise
            print(f"Retrying doc {doc_id} ({attempt}/{MAX_RETRIES}) due to: {exc}")
            time.sleep(RETRY_DELAY_SECONDS)

    raise last_exc  # type: ignore[misc]


def choose_best_value(candidates: list[str], fallback: str) -> str:
    counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized:
            counts[normalized] += 1

    if not counts:
        return fallback

    return max(
        counts.items(),
        key=lambda item: (item[1], item[0] == fallback, len(item[0]), item[0]),
    )[0]


def merge_group_normalization_results(
    group_results: list[list[dict[str, str]]],
    original_terms: list[Any],
    original_triples: list[dict[str, Any]],
) -> list[dict[str, str]]:
    normalized_votes: dict[str, list[str]] = defaultdict(list)
    type_votes: dict[str, list[str]] = defaultdict(list)

    for items in group_results:
        for item in items:
            original = str(item.get("original", "")).strip()
            normalized = str(item.get("normalized", "")).strip()
            term_type = str(item.get("type", "")).strip()
            if not original:
                continue
            normalized_votes[original].append(normalized or original)
            if term_type:
                type_votes[original].append(term_type)

    all_originals = unique_preserve_order(
        [str(term).strip() for term in original_terms if str(term).strip()]
        + [
            str(triple.get(key, "")).strip()
            for triple in original_triples
            for key in ("subject", "relation", "object")
            if str(triple.get(key, "")).strip()
        ]
    )

    merged_items: list[dict[str, str]] = []
    for original in all_originals:
        normalized = choose_best_value(normalized_votes.get(original, []), original)
        inferred_type = choose_best_value(type_votes.get(original, []), "")
        merged_items.append(
            {
                "original": original,
                "normalized": normalized,
                "type": inferred_type,
            }
        )

    return merged_items


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
    valid_count = 0
    for triple in triples:
        if (
            str(triple.get("subject", "")).strip()
            and str(triple.get("relation", "")).strip()
            and str(triple.get("object", "")).strip()
        ):
            valid_count += 1
    return valid_count


def build_normalization_maps(
    normalized_terms: list[dict[str, Any]],
    original_terms: list[Any],
    original_triples: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    term_map: dict[str, str] = {}
    type_map: dict[str, str] = {}

    for item in normalized_terms:
        original = str(item.get("original", "")).strip()
        normalized = str(item.get("normalized", "")).strip()
        term_type = str(item.get("type", "")).strip()
        if not original:
            continue
        term_map[original] = normalized or original
        if normalized and term_type:
            type_map[normalized] = term_type

    for term in original_terms:
        term_text = str(term).strip()
        if term_text and term_text not in term_map:
            term_map[term_text] = term_text

    for triple in original_triples:
        for key in ("subject", "relation", "object"):
            value = str(triple.get(key, "")).strip()
            if value and value not in term_map:
                term_map[value] = value

    return term_map, type_map


def normalize_evidence_from_first_layer(triple: dict[str, Any]) -> list[dict[str, str]]:
    chunk = str(triple.get("chunk", "")).strip()
    context = str(triple.get("context", "")).strip()
    if not chunk and not context:
        return []
    return [{"chunk": chunk, "context": context}]


def aggregate_updated_triples(
    original_triples: list[dict[str, Any]],
    term_map: dict[str, str],
) -> list[dict[str, Any]]:
    aggregated: dict[tuple[str, str, str], dict[str, Any]] = {}

    for triple in original_triples:
        subject = term_map.get(str(triple.get("subject", "")).strip(), str(triple.get("subject", "")).strip())
        relation = term_map.get(str(triple.get("relation", "")).strip(), str(triple.get("relation", "")).strip())
        obj = term_map.get(str(triple.get("object", "")).strip(), str(triple.get("object", "")).strip())

        if not (subject and relation and obj):
            continue

        key = (subject, relation, obj)
        entry = aggregated.setdefault(
            key,
            {
                "subject": subject,
                "relation": relation,
                "object": obj,
                "evidence": [],
            },
        )

        for evidence in normalize_evidence_from_first_layer(triple):
            evidence_key = (evidence["chunk"], evidence["context"])
            if evidence_key not in {
                (item.get("chunk", ""), item.get("context", ""))
                for item in entry["evidence"]
            }:
                entry["evidence"].append(evidence)

    return list(aggregated.values())


def build_record(
    domain: str,
    doc_id: str,
    normalized_terms: list[dict[str, Any]],
    updated_triples: list[dict[str, Any]],
    note: str = "",
) -> dict[str, Any]:
    return {
        "模型": MODEL_OUTPUT_NAME,
        "领域": domain,
        "文档ID": doc_id,
        "配置轮次": RUN_NAME,
        "标准化术语数": len(normalized_terms),
        "归并后关系数": len(updated_triples),
        "有效归并后关系数": count_valid_triples(updated_triples),
        "备注": note,
    }


def run() -> None:
    client = build_client()
    input_files = iter_input_files()
    if not input_files:
        raise ValueError(f"输入目录中没有 JSON 数据: {INPUT_JSON_DIR}")

    print(f"Found {len(input_files)} input JSON files.")
    print(f"RUN_NAME={RUN_NAME}")

    prepared_inputs: list[dict[str, Any]] = []
    total_groups = 0
    for input_path in input_files:
        doc_id, domain, terms, triples = load_input_result(input_path)
        grouped_inputs = build_grouped_inputs(terms, triples)
        prepared_inputs.append(
            {
                "input_path": input_path,
                "doc_id": doc_id,
                "domain": domain,
                "terms": terms,
                "triples": triples,
                "grouped_inputs": grouped_inputs,
            }
        )
        total_groups += len(grouped_inputs)

    print(f"Total group requests to run: {total_groups}")
    progress = tqdm(total=total_groups, desc=f"{MODEL_OUTPUT_NAME} {RUN_NAME}", unit="group")

    for item in prepared_inputs:
        input_path = item["input_path"]
        doc_id = item["doc_id"]
        domain = item["domain"]
        terms = item["terms"]
        triples = item["triples"]
        grouped_inputs = item["grouped_inputs"]
        print(f"Processing {domain}/{doc_id}")
        note = ""
        group_prompt_dir = PROMPT_OUTPUT_DIR / domain / doc_id
        raw_group_outputs: list[dict[str, Any]] = []
        normalized_group_results: list[list[dict[str, str]]] = []

        try:
            for group in grouped_inputs:
                group_index = int(group["group_index"])
                print(f"  Group {group_index}/{len(grouped_inputs)}")
                group_prompt = build_prompt(domain, group["terms"], group["triples"])
                save_text(group_prompt, group_prompt_dir / f"group_{group_index:02d}.txt")

                group_result, group_raw_text = call_llm_with_retry(
                    client,
                    group_prompt,
                    f"{doc_id}/group_{group_index:02d}",
                )
                group_normalized_terms = group_result.get("normalized_terms", [])
                normalized_group_results.append(group_normalized_terms)
                raw_group_outputs.append(
                    {
                        "group_index": group_index,
                        "terms": group["terms"],
                        "triples": group["triples"],
                        "normalized_terms": group_normalized_terms,
                        "_raw_text": group_raw_text,
                    }
                )
                progress.update(1)

            normalized_terms = merge_group_normalization_results(normalized_group_results, terms, triples)
            term_map, type_map = build_normalization_maps(normalized_terms, terms, triples)
            updated_triples = aggregate_updated_triples(triples, term_map)
        except Exception as exc:
            normalized_terms = []
            term_map = {}
            type_map = {}
            updated_triples = []
            raw_group_outputs.append(
                {
                    "group_index": -1,
                    "error": str(exc),
                }
            )
            note = str(exc)

        full_result = {
            "doc_id": doc_id,
            "domain": domain,
            "input_json": str(input_path),
            "group_triple_size": GROUP_TRIPLE_SIZE,
            "group_term_limit": GROUP_TERM_LIMIT,
            "group_count": len(grouped_inputs),
            "group_results": raw_group_outputs,
            "normalized_terms": normalized_terms,
            "term_map": term_map,
            "type_map": type_map,
            "updated_triples": updated_triples,
            "error": note,
        }

        concept_input_result = {
            "doc_id": doc_id,
            "domain": domain,
            "source_run": RUN_NAME,
            "source_json": str(RAW_OUTPUT_DIR / domain / f"{doc_id}.json"),
            "normalized_terms": normalized_terms,
            "term_map": term_map,
            "type_map": type_map,
            "updated_triples": updated_triples,
        }

        save_json(full_result, RAW_OUTPUT_DIR / domain / f"{doc_id}.json")
        save_json(concept_input_result, CONCEPT_INPUT_DIR / domain / f"{doc_id}.json")
        append_csv(build_record(domain, doc_id, normalized_terms, updated_triples, note), SUMMARY_CSV)
        time.sleep(SLEEP_SECONDS)

    progress.close()
    print("Done!")


if __name__ == "__main__":
    run()
