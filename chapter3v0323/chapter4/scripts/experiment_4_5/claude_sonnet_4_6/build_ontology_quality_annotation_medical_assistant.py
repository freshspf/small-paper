import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
ANNOTATION_DIR = DATA_DIR / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"

PREPROCESSED_DIR = OUTPUTS_DIR / "preprocessed_inputs" / "experiment_4_5_pdf3" / "medical"
BASELINE_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "baseline_chunk_json" / "medical"
THREE_STAGE_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json" / "medical"
THREE_STAGE_INPUT_DIR = OUTPUTS_DIR / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_from_term_based_chunk_json" / "medical"
PDF_DIR = DATA_DIR / "raw" / "pdf3" / "medical"

OUTPUT_CSV = ANNOTATION_DIR / "ontology_quality_annotation_medical_assistant.csv"

HEADERS = [
    "方法",
    "文档ID",
    "来源PDF",
    "公理类型",
    "项1",
    "项2",
    "是否被原文明确支持",
    "是否为合理扩展",
    "命名是否规范",
    "是否建议保留",
    "证据页码",
    "证据原文",
    "备注",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: str) -> str:
    return " ".join(text.split())


def shorten(text: str, limit: int = 220) -> str:
    text = compact(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def split_identifier(text: str) -> list[str]:
    raw = re.sub(r"[_\\-]+", " ", text)
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\\1 \\2", raw)
    raw = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\\1 \\2", raw)
    parts = [part.lower() for part in raw.split() if part.strip()]
    return parts


def contains_term(text: str, term: str) -> bool:
    haystack = compact(text).lower()
    if not haystack:
        return False

    tokens = split_identifier(term)
    if not tokens:
        return False

    joined = " ".join(tokens)
    if joined in haystack:
        return True

    if len(tokens) == 1:
        return tokens[0] in haystack

    return all(token in haystack for token in tokens[: min(3, len(tokens))])


def class_name_ok(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", name))


def property_name_ok(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z][A-Za-z0-9]*", name))


def term_name_ok(axiom_type: str, item1: str) -> bool:
    if axiom_type == "Property":
        return property_name_ok(item1)
    return class_name_ok(item1)


def pair_name_ok(axiom_type: str, item1: str, item2: str) -> bool:
    if axiom_type in {"subPropertyOf"}:
        return property_name_ok(item1) and property_name_ok(item2)
    if axiom_type in {"domain", "range"}:
        return property_name_ok(item1) and class_name_ok(item2)
    return class_name_ok(item1) and class_name_ok(item2)


@lru_cache(maxsize=None)
def load_preprocessed_chunks(doc_id: str) -> dict[str, dict[str, str]]:
    path = PREPROCESSED_DIR / f"{doc_id}.json"
    data = load_json(path)
    result: dict[str, dict[str, str]] = {}
    for item in data:
        chunk_id = str(item.get("id", "")).strip()
        meta = item.get("metadata", {}) or {}
        if not chunk_id:
            continue
        result[chunk_id] = {
            "text": str(item.get("text", "")).strip(),
            "page_start": str(meta.get("page_start", "")).strip(),
            "page_end": str(meta.get("page_end", "")).strip(),
            "section_title": str(meta.get("section_title", "")).strip(),
        }
    return result


@lru_cache(maxsize=None)
def load_baseline(doc_id: str) -> dict[str, Any]:
    return load_json(BASELINE_DIR / f"{doc_id}.json")


@lru_cache(maxsize=None)
def load_three_stage(doc_id: str) -> dict[str, Any]:
    return load_json(THREE_STAGE_DIR / f"{doc_id}.json")


@lru_cache(maxsize=None)
def load_three_stage_input(doc_id: str) -> dict[str, Any]:
    return load_json(THREE_STAGE_INPUT_DIR / f"{doc_id}.json")


def page_range(chunk_info: dict[str, str]) -> str:
    start = chunk_info.get("page_start", "")
    end = chunk_info.get("page_end", "")
    if start and end and start != end:
        return f"{start}-{end}"
    return start or end


def baseline_evidence(doc_id: str, axiom_type: str, item1: str, item2: str) -> tuple[list[str], list[str], list[str]]:
    data = load_baseline(doc_id)
    pre_chunks = load_preprocessed_chunks(doc_id)
    chunk_ids: list[str] = []
    contexts: list[str] = []
    pages: list[str] = []

    for chunk_result in data.get("chunk_results", []):
        chunk_id = str(chunk_result.get("chunk_id", "")).strip()
        matched = False
        if axiom_type == "Class":
            matched = item1 in chunk_result.get("classes", [])
        elif axiom_type == "Property":
            matched = item1 in chunk_result.get("properties", [])
        elif axiom_type == "subClassOf":
            matched = any(
                str(x.get("sub", "")).strip() == item1 and str(x.get("super", "")).strip() == item2
                for x in chunk_result.get("subClassOf", [])
            )
        elif axiom_type == "subPropertyOf":
            matched = any(
                str(x.get("sub", "")).strip() == item1 and str(x.get("super", "")).strip() == item2
                for x in chunk_result.get("subPropertyOf", [])
            )
        elif axiom_type == "domain":
            matched = any(
                str(x.get("property", "")).strip() == item1 and str(x.get("class", "")).strip() == item2
                for x in chunk_result.get("domain", [])
            )
        elif axiom_type == "range":
            matched = any(
                str(x.get("property", "")).strip() == item1 and str(x.get("class", "")).strip() == item2
                for x in chunk_result.get("range", [])
            )

        if matched and chunk_id:
            chunk_ids.append(chunk_id)
            info = pre_chunks.get(chunk_id, {})
            if info.get("text"):
                contexts.append(info["text"])
            if page_range(info):
                pages.append(page_range(info))

    return list(dict.fromkeys(chunk_ids)), list(dict.fromkeys(contexts)), list(dict.fromkeys(pages))


def three_stage_evidence(doc_id: str, axiom_type: str, item1: str, item2: str) -> tuple[list[str], list[str], list[str]]:
    data = load_three_stage_input(doc_id)
    pre_chunks = load_preprocessed_chunks(doc_id)
    chunk_ids: list[str] = []
    contexts: list[str] = []
    pages: list[str] = []

    for triple in data.get("updated_triples", []):
        s = str(triple.get("subject", "")).strip()
        r = str(triple.get("relation", "")).strip()
        o = str(triple.get("object", "")).strip()
        matched = False

        if axiom_type == "Class":
            matched = item1 in {s, o}
        elif axiom_type == "Property":
            matched = item1 == r
        elif axiom_type == "subClassOf":
            matched = item1 in {s, o} or item2 in {s, o}
        elif axiom_type == "subPropertyOf":
            matched = item1 == r or item2 == r
        elif axiom_type == "domain":
            matched = item1 == r and item2 == s
        elif axiom_type == "range":
            matched = item1 == r and item2 == o

        if not matched:
            continue

        for evidence in triple.get("evidence", []):
            chunk_id = str(evidence.get("chunk", "")).strip()
            context = str(evidence.get("context", "")).strip()
            if chunk_id:
                chunk_ids.append(chunk_id)
                info = pre_chunks.get(chunk_id, {})
                if page_range(info):
                    pages.append(page_range(info))
            if context:
                contexts.append(context)

    return list(dict.fromkeys(chunk_ids)), list(dict.fromkeys(contexts)), list(dict.fromkeys(pages))


def annotate_row(method: str, doc_id: str, axiom_type: str, item1: str, item2: str) -> dict[str, str]:
    pdf_path = str(PDF_DIR / f"{doc_id}.pdf")

    if method == "baseline":
        chunk_ids, contexts, pages = baseline_evidence(doc_id, axiom_type, item1, item2)
    else:
        chunk_ids, contexts, pages = three_stage_evidence(doc_id, axiom_type, item1, item2)

    evidence_text = " || ".join(shorten(x) for x in contexts[:2])
    page_text = " | ".join(pages[:2])

    if axiom_type in {"Class", "Property"}:
        explicit = "是" if any(contains_term(ctx, item1) for ctx in contexts) else "否"
    elif axiom_type in {"subClassOf", "subPropertyOf"}:
        explicit = "否"
    elif axiom_type == "domain":
        explicit = "是" if any(contains_term(ctx, item1) and contains_term(ctx, item2) for ctx in contexts) else "否"
    elif axiom_type == "range":
        explicit = "是" if any(contains_term(ctx, item1) and contains_term(ctx, item2) for ctx in contexts) else "否"
    else:
        explicit = "否"

    if axiom_type in {"Class", "Property"}:
        reasonable = "是" if contexts else "否"
    elif axiom_type in {"domain", "range"}:
        reasonable = "是" if contexts else "否"
    else:
        reasonable = "是" if contexts else "否"

    if axiom_type in {"Class", "Property"}:
        naming_ok = "是" if term_name_ok(axiom_type, item1) else "否"
    else:
        naming_ok = "是" if pair_name_ok(axiom_type, item1, item2) else "否"

    if explicit == "是":
        keep = "是"
    elif reasonable == "是" and naming_ok == "是":
        keep = "是"
    else:
        keep = "否"

    notes: list[str] = []
    if chunk_ids:
        notes.append(f"evidence chunks: {', '.join(chunk_ids[:3])}")
    if explicit == "否" and reasonable == "是":
        notes.append("更接近建模扩展而非原文显式陈述")
    if naming_ok == "否":
        notes.append("命名形式不规范")
    if not contexts:
        notes.append("未检索到稳定上下文证据")

    return {
        "方法": method,
        "文档ID": doc_id,
        "来源PDF": pdf_path,
        "公理类型": axiom_type,
        "项1": item1,
        "项2": item2,
        "是否被原文明确支持": explicit,
        "是否为合理扩展": reasonable,
        "命名是否规范": naming_ok,
        "是否建议保留": keep,
        "证据页码": page_text,
        "证据原文": evidence_text,
        "备注": "；".join(notes),
    }


def rows_from_result(method: str, path: Path) -> list[dict[str, str]]:
    data = load_json(path)
    doc_id = str(data.get("doc_id", "")).strip() or path.stem
    rows: list[dict[str, str]] = []

    for class_name in data.get("classes", []):
        item1 = str(class_name).strip()
        if item1:
            rows.append(annotate_row(method, doc_id, "Class", item1, ""))

    for property_name in data.get("properties", []):
        item1 = str(property_name).strip()
        if item1:
            rows.append(annotate_row(method, doc_id, "Property", item1, ""))

    for item in data.get("subClassOf", []):
        rows.append(
            annotate_row(
                method,
                doc_id,
                "subClassOf",
                str(item.get("sub", "")).strip(),
                str(item.get("super", "")).strip(),
            )
        )

    for item in data.get("subPropertyOf", []):
        rows.append(
            annotate_row(
                method,
                doc_id,
                "subPropertyOf",
                str(item.get("sub", "")).strip(),
                str(item.get("super", "")).strip(),
            )
        )

    for item in data.get("domain_axioms", []):
        rows.append(
            annotate_row(
                method,
                doc_id,
                "domain",
                str(item.get("property", "")).strip(),
                str(item.get("class", "")).strip(),
            )
        )

    for item in data.get("range_axioms", []):
        rows.append(
            annotate_row(
                method,
                doc_id,
                "range",
                str(item.get("property", "")).strip(),
                str(item.get("class", "")).strip(),
            )
        )

    return rows


def main() -> None:
    rows: list[dict[str, str]] = []
    for method, directory in [("baseline", BASELINE_DIR), ("three_stage", THREE_STAGE_DIR)]:
        for path in sorted(directory.glob("*.json")):
            rows.extend(rows_from_result(method, path))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
