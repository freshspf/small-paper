import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[3]
ANNOTATION_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"
OUTPUTS_DIR = BASE_DIR / "outputs"

INPUT_TABLE = ANNOTATION_DIR / "final_ontology_annotation_comparison_medical.csv"
OUTPUT_TABLE = ANNOTATION_DIR / "final_ontology_preannotation_comparison_medical.csv"
PREPROCESSED_DIR = OUTPUTS_DIR / "preprocessed_inputs" / "experiment_4_5_pdf3" / "medical"
BASELINE_OUTPUT_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "baseline_chunk_json" / "medical"
THREE_STAGE_INPUT_DIR = OUTPUTS_DIR / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_from_term_based_chunk_json" / "medical"

EXTRA_COLUMNS = [
    "证据chunk",
    "证据context",
    "建议判定",
    "建议理由",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_preprocessed_chunks(doc_id: str) -> dict[str, dict[str, str]]:
    path = PREPROCESSED_DIR / f"{doc_id}.json"
    data = load_json(path)
    chunk_map: dict[str, dict[str, str]] = {}
    for item in data:
        chunk_id = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()
        section = str(item.get("metadata", {}).get("section_title", "")).strip()
        if chunk_id:
            chunk_map[chunk_id] = {
                "text": text,
                "section": section,
            }
    return chunk_map


@lru_cache(maxsize=None)
def load_baseline_output(doc_id: str) -> dict[str, Any]:
    return load_json(BASELINE_OUTPUT_DIR / f"{doc_id}.json")


@lru_cache(maxsize=None)
def load_three_stage_input(doc_id: str) -> dict[str, Any]:
    return load_json(THREE_STAGE_INPUT_DIR / f"{doc_id}.json")


def shorten(text: str, limit: int = 500) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def join_evidence(chunks: list[str], contexts: list[str]) -> tuple[str, str]:
    chunk_text = " | ".join(chunks[:3])
    context_text = " || ".join(shorten(item) for item in contexts[:3])
    return chunk_text, context_text


def find_baseline_evidence(doc_id: str, row: dict[str, str]) -> tuple[list[str], list[str], str, str]:
    data = load_baseline_output(doc_id)
    chunk_map = load_preprocessed_chunks(doc_id)
    axiom_type = row["公理类型"]
    subject = row["subject"].strip()
    predicate = row["predicate"].strip()
    object_value = row["object"].strip()

    matched_chunks: list[str] = []
    matched_contexts: list[str] = []

    for chunk_result in data.get("chunk_results", []):
        chunk_id = str(chunk_result.get("chunk_id", "")).strip()
        matched = False

        if axiom_type == "Class":
            matched = subject in chunk_result.get("classes", [])
        elif axiom_type == "Property":
            matched = subject in chunk_result.get("properties", [])
        elif axiom_type == "subClassOf":
            matched = any(
                str(item.get("sub", "")).strip() == subject
                and str(item.get("super", "")).strip() == object_value
                for item in chunk_result.get("subClassOf", [])
            )
        elif axiom_type == "subPropertyOf":
            matched = any(
                str(item.get("sub", "")).strip() == subject
                and str(item.get("super", "")).strip() == object_value
                for item in chunk_result.get("subPropertyOf", [])
            )
        elif axiom_type == "domain":
            matched = any(
                str(item.get("property", "")).strip() == subject
                and str(item.get("class", "")).strip() == object_value
                for item in chunk_result.get("domain", [])
            )
        elif axiom_type == "range":
            matched = any(
                str(item.get("property", "")).strip() == subject
                and str(item.get("class", "")).strip() == object_value
                for item in chunk_result.get("range", [])
            )

        if matched and chunk_id:
            matched_chunks.append(chunk_id)
            context = chunk_map.get(chunk_id, {}).get("text", "")
            if context:
                matched_contexts.append(context)

    if matched_chunks:
        if axiom_type in {"Class", "Property"}:
            label = "待复核"
            reason = "该公理在 baseline 的局部 chunk 输出中出现，但声明类/属性是否合理仍需人工结合全文确认。"
        else:
            label = "待复核"
            reason = "该公理在 baseline 的局部 chunk 输出中出现，已附上对应 chunk 原文，建议人工核对是否被原文直接支持。"
    else:
        label = "可能错误"
        reason = "未在 baseline 的任何 chunk 局部输出中定位到该公理，疑似仅由最终聚合引入或对齐失败。"

    return matched_chunks, matched_contexts, label, reason


def find_three_stage_evidence(doc_id: str, row: dict[str, str]) -> tuple[list[str], list[str], str, str]:
    data = load_three_stage_input(doc_id)
    axiom_type = row["公理类型"]
    subject = row["subject"].strip()
    object_value = row["object"].strip()
    predicate = row["predicate"].strip()

    matched_chunks: list[str] = []
    matched_contexts: list[str] = []

    for triple in data.get("updated_triples", []):
        triple_subject = str(triple.get("subject", "")).strip()
        triple_relation = str(triple.get("relation", "")).strip()
        triple_object = str(triple.get("object", "")).strip()
        evidence_items = triple.get("evidence", [])

        matched = False
        if axiom_type == "Class":
            matched = subject in {triple_subject, triple_object}
        elif axiom_type == "Property":
            matched = subject == triple_relation
        elif axiom_type == "subClassOf":
            matched = subject in {triple_subject, triple_object} or object_value in {triple_subject, triple_object}
        elif axiom_type == "subPropertyOf":
            matched = subject == triple_relation or object_value == triple_relation
        elif axiom_type == "domain":
            matched = subject == triple_relation and object_value == triple_subject
        elif axiom_type == "range":
            matched = subject == triple_relation and object_value == triple_object

        if not matched:
            continue

        for evidence in evidence_items:
            chunk = str(evidence.get("chunk", "")).strip()
            context = str(evidence.get("context", "")).strip()
            if chunk:
                matched_chunks.append(chunk)
            if context:
                matched_contexts.append(context)

    matched_chunks = list(dict.fromkeys(matched_chunks))
    matched_contexts = list(dict.fromkeys(matched_contexts))

    if axiom_type in {"domain", "range"} and matched_contexts:
        label = "较高置信"
        reason = "该 domain/range 公理可在第二层归并后的 evidence 三元组中找到同属性同角色的直接上下文支撑。"
    elif axiom_type == "Property" and matched_contexts:
        label = "较高置信"
        reason = "该属性在第二层 evidence 三元组中被直接用作 relation。"
    elif axiom_type == "Class" and matched_contexts:
        label = "待复核"
        reason = "该类名在第二层 evidence 支撑的三元组中出现，但是否应建模为类仍需人工判断。"
    elif axiom_type in {"subClassOf", "subPropertyOf"} and matched_contexts:
        label = "待复核"
        reason = "存在相关上下文，但层级关系通常是建模推断，不一定在原文显式出现，需人工复核。"
    else:
        label = "可能错误"
        reason = "未在第二层 evidence 支撑的三元组中检索到稳定对应证据。"

    return matched_chunks, matched_contexts, label, reason


def main() -> None:
    with INPUT_TABLE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or []) + EXTRA_COLUMNS
        rows: list[dict[str, str]] = []

        for row in reader:
            doc_id = row["文档ID"].strip()
            method = row["方法"].strip()
            if method == "baseline":
                chunks, contexts, label, reason = find_baseline_evidence(doc_id, row)
            else:
                chunks, contexts, label, reason = find_three_stage_evidence(doc_id, row)

            row["证据chunk"], row["证据context"] = join_evidence(chunks, contexts)
            row["建议判定"] = label
            row["建议理由"] = reason
            rows.append(row)

    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_TABLE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to: {OUTPUT_TABLE}")


if __name__ == "__main__":
    main()
