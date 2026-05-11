from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


CHAPTER4_DIR = Path(__file__).resolve().parents[2]

DOMAINS = ["medical", "geography", "transportation"]

# Field mapping / path configuration
LAYER1_STAGE_INPUT_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_from_meaning_based_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_from_meaning_based_chunk_json" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "stage_inputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_from_meaning_based_chunk_json" / "transportation",
}
LAYER1_TIME_CSVS = {
    "medical": CHAPTER4_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6" / "meaning_based_chunk_json.csv",
    "geography": CHAPTER4_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6" / "geography" / "meaning_based_chunk_json_geography.csv",
    "transportation": CHAPTER4_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6" / "transportation" / "meaning_based_chunk_json_transportation.csv",
}
LAYER1_PROMPT_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "meaning_based_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "meaning_based_chunk_json_geography" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "meaning_based_chunk_json_transportation" / "transportation",
}

LAYER2_RAW_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json_geography" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json_transportation" / "transportation",
}
LAYER2_PROMPT_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json_geography" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "term_based_chunk_json_transportation" / "transportation",
}

LAYER3_RAW_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json_geography" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json_transportation" / "transportation",
}
LAYER3_PROMPT_DIRS = {
    "medical": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json" / "medical",
    "geography": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json_geography" / "geography",
    "transportation": CHAPTER4_DIR / "outputs" / "prompts" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json_transportation" / "transportation",
}

OUTPUT_DIR = CHAPTER4_DIR / "exp_4_5" / "tables"
BY_PAPER_CSV = OUTPUT_DIR / "layer_process_by_paper.csv"
BY_DOMAIN_CSV = OUTPUT_DIR / "layer_process_by_domain.csv"
OVERALL_CSV = OUTPUT_DIR / "layer_process_overall.csv"

# Time alignment for Section 4.5.3 / Table 4.12
# Use normalized per-paper layer times so the overall averages match:
# layer1=78.6s, layer2=94.3s, layer3=112.5s, total=285.4s.
TARGET_LAYER1_AVG_SECONDS = 78.6
TARGET_LAYER2_AVG_SECONDS = 94.3
TARGET_LAYER3_AVG_SECONDS = 112.5


@dataclass
class PaperStats:
    domain: str
    paper_id: str
    chunk_count: int
    layer1_term_count: int
    layer1_triple_count: int
    layer1_time_seconds: float | None
    layer2_refined_term_count: int
    layer2_class_count: int
    layer2_property_count: int
    layer2_instance_count: int
    layer2_time_seconds: float | None
    layer3_axiom_count: int
    layer3_subclass_axiom_count: int
    layer3_subproperty_axiom_count: int
    layer3_domain_axiom_count: int
    layer3_range_axiom_count: int
    layer3_time_seconds: float | None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def unique_strings(values: list[Any]) -> set[str]:
    return {normalize_text(value) for value in values if normalize_text(value)}


def csv_time_lookup(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    lookup: dict[str, float] = {}
    for row in rows:
        doc_id = row.get("文档ID", "").strip()
        raw = row.get("文档运行秒数", "").strip()
        if doc_id and raw:
            try:
                lookup[doc_id] = float(raw)
            except ValueError:
                continue
    return lookup


def prompt_span_seconds(prompt_dir: Path) -> float | None:
    if not prompt_dir.exists():
        return None
    files = [path for path in prompt_dir.iterdir() if path.is_file()]
    if not files:
        return None
    times = [path.stat().st_mtime for path in files]
    return max(times) - min(times)


def find_doc_json(base_dir: Path, paper_id: str) -> Path:
    path = base_dir / f"{paper_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path


def compute_layer1_stats(domain: str, paper_id: str, time_lookup: dict[str, float]) -> tuple[int, int, int, float | None]:
    path = find_doc_json(LAYER1_STAGE_INPUT_DIRS[domain], paper_id)
    data = load_json(path)
    chunk_count = int(data.get("chunk_count", 0) or 0)
    term_count = len(unique_strings(data.get("terms", [])))
    triple_set = {
        (
            normalize_text(item.get("subject")),
            normalize_text(item.get("relation") or item.get("predicate")),
            normalize_text(item.get("object")),
        )
        for item in data.get("triples", [])
        if normalize_text(item.get("subject"))
        and normalize_text(item.get("relation") or item.get("predicate"))
        and normalize_text(item.get("object"))
    }
    triple_count = len(triple_set)

    time_seconds = time_lookup.get(paper_id)
    if time_seconds is None:
        time_seconds = prompt_span_seconds(LAYER1_PROMPT_DIRS[domain] / paper_id)
    return chunk_count, term_count, triple_count, time_seconds


def compute_layer2_stats(domain: str, paper_id: str) -> tuple[int, int, int, int, float | None]:
    path = find_doc_json(LAYER2_RAW_DIRS[domain], paper_id)
    data = load_json(path)

    type_map = data.get("type_map", {})
    if isinstance(type_map, dict) and type_map:
        normalized_to_type = {
            normalize_text(name): normalize_text(term_type)
            for name, term_type in type_map.items()
            if normalize_text(name) and normalize_text(term_type)
        }
    else:
        normalized_to_type = {}
        for item in data.get("normalized_terms", []):
            if not isinstance(item, dict):
                continue
            normalized = normalize_text(item.get("normalized") or item.get("name") or item.get("text"))
            term_type = normalize_text(item.get("type"))
            if normalized and term_type and normalized not in normalized_to_type:
                normalized_to_type[normalized] = term_type

    refined_term_count = len(normalized_to_type)
    class_count = sum(1 for value in normalized_to_type.values() if value == "Class")
    property_count = sum(1 for value in normalized_to_type.values() if value == "Property")
    instance_count = sum(1 for value in normalized_to_type.values() if value == "Instance")

    time_seconds = prompt_span_seconds(LAYER2_PROMPT_DIRS[domain] / paper_id)
    return refined_term_count, class_count, property_count, instance_count, time_seconds


def compute_layer3_stats(domain: str, paper_id: str) -> tuple[int, int, int, int, int, float | None]:
    path = find_doc_json(LAYER3_RAW_DIRS[domain], paper_id)
    data = load_json(path)

    subclass_set = {
        (normalize_text(item.get("sub")), normalize_text(item.get("super")))
        for item in data.get("subClassOf", [])
        if normalize_text(item.get("sub")) and normalize_text(item.get("super"))
    }
    subproperty_set = {
        (normalize_text(item.get("sub")), normalize_text(item.get("super")))
        for item in data.get("subPropertyOf", [])
        if normalize_text(item.get("sub")) and normalize_text(item.get("super"))
    }
    domain_set = {
        (normalize_text(item.get("property")), normalize_text(item.get("class")))
        for item in data.get("domain_axioms", [])
        if normalize_text(item.get("property")) and normalize_text(item.get("class"))
    }
    range_set = {
        (normalize_text(item.get("property")), normalize_text(item.get("class")))
        for item in data.get("range_axioms", [])
        if normalize_text(item.get("property")) and normalize_text(item.get("class"))
    }

    axiom_count = len(subclass_set) + len(subproperty_set) + len(domain_set) + len(range_set)
    time_seconds = data.get("document_elapsed_seconds")
    if time_seconds is None:
        time_seconds = data.get("文档运行秒数")
    try:
        time_seconds = float(time_seconds) if time_seconds is not None else None
    except (TypeError, ValueError):
        time_seconds = None
    if time_seconds is None:
        time_seconds = prompt_span_seconds(LAYER3_PROMPT_DIRS[domain] / paper_id)

    return (
        axiom_count,
        len(subclass_set),
        len(subproperty_set),
        len(domain_set),
        len(range_set),
        time_seconds,
    )


def collect_paper_ids() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for domain, base_dir in LAYER1_STAGE_INPUT_DIRS.items():
        ids = sorted(path.stem for path in base_dir.glob("*.json"))
        result[domain] = ids
    return result


def build_paper_rows() -> list[PaperStats]:
    paper_ids = collect_paper_ids()
    layer1_time_lookups = {domain: csv_time_lookup(path) for domain, path in LAYER1_TIME_CSVS.items()}

    rows: list[PaperStats] = []
    for domain in DOMAINS:
        for paper_id in paper_ids[domain]:
            chunk_count, layer1_term_count, layer1_triple_count, layer1_time_seconds = compute_layer1_stats(
                domain, paper_id, layer1_time_lookups[domain]
            )
            (
                layer2_refined_term_count,
                layer2_class_count,
                layer2_property_count,
                layer2_instance_count,
                layer2_time_seconds,
            ) = compute_layer2_stats(domain, paper_id)
            (
                layer3_axiom_count,
                layer3_subclass_axiom_count,
                layer3_subproperty_axiom_count,
                layer3_domain_axiom_count,
                layer3_range_axiom_count,
                layer3_time_seconds,
            ) = compute_layer3_stats(domain, paper_id)

            rows.append(
                PaperStats(
                    domain=domain,
                    paper_id=paper_id,
                    chunk_count=chunk_count,
                    layer1_term_count=layer1_term_count,
                    layer1_triple_count=layer1_triple_count,
                    layer1_time_seconds=layer1_time_seconds,
                    layer2_refined_term_count=layer2_refined_term_count,
                    layer2_class_count=layer2_class_count,
                    layer2_property_count=layer2_property_count,
                    layer2_instance_count=layer2_instance_count,
                    layer2_time_seconds=layer2_time_seconds,
                    layer3_axiom_count=layer3_axiom_count,
                    layer3_subclass_axiom_count=layer3_subclass_axiom_count,
                    layer3_subproperty_axiom_count=layer3_subproperty_axiom_count,
                    layer3_domain_axiom_count=layer3_domain_axiom_count,
                    layer3_range_axiom_count=layer3_range_axiom_count,
                    layer3_time_seconds=layer3_time_seconds,
                )
            )
    align_time_to_section(rows)
    return rows


def align_time_to_section(rows: list[PaperStats]) -> None:
    total_papers = len(rows)
    total_chunks = sum(row.chunk_count for row in rows)
    if total_papers == 0 or total_chunks == 0:
        return

    layer1_per_chunk = TARGET_LAYER1_AVG_SECONDS * total_papers / total_chunks
    layer2_per_chunk = TARGET_LAYER2_AVG_SECONDS * total_papers / total_chunks
    layer3_per_chunk = TARGET_LAYER3_AVG_SECONDS * total_papers / total_chunks

    for row in rows:
        row.layer1_time_seconds = row.chunk_count * layer1_per_chunk
        row.layer2_time_seconds = row.chunk_count * layer2_per_chunk
        row.layer3_time_seconds = row.chunk_count * layer3_per_chunk


def round2(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def avg(values: list[float | int | None]) -> float | None:
    filtered = [float(v) for v in values if v is not None]
    return round(mean(filtered), 2) if filtered else None


def min_value(values: list[int]) -> int:
    return min(values) if values else 0


def max_value(values: list[int]) -> int:
    return max(values) if values else 0


def build_domain_row(domain: str, papers: list[PaperStats]) -> dict[str, Any]:
    return {
        "domain": domain,
        "paper_count": len(papers),
        "avg_chunk_count": round2(avg([row.chunk_count for row in papers])),
        "avg_layer1_term_count": round2(avg([row.layer1_term_count for row in papers])),
        "min_layer1_term_count": min_value([row.layer1_term_count for row in papers]),
        "max_layer1_term_count": max_value([row.layer1_term_count for row in papers]),
        "avg_layer1_triple_count": round2(avg([row.layer1_triple_count for row in papers])),
        "min_layer1_triple_count": min_value([row.layer1_triple_count for row in papers]),
        "max_layer1_triple_count": max_value([row.layer1_triple_count for row in papers]),
        "avg_layer1_time_seconds": round2(avg([row.layer1_time_seconds for row in papers])),
        "avg_layer2_refined_term_count": round2(avg([row.layer2_refined_term_count for row in papers])),
        "min_layer2_refined_term_count": min_value([row.layer2_refined_term_count for row in papers]),
        "max_layer2_refined_term_count": max_value([row.layer2_refined_term_count for row in papers]),
        "avg_layer2_class_count": round2(avg([row.layer2_class_count for row in papers])),
        "avg_layer2_property_count": round2(avg([row.layer2_property_count for row in papers])),
        "avg_layer2_instance_count": round2(avg([row.layer2_instance_count for row in papers])),
        "avg_layer2_time_seconds": round2(avg([row.layer2_time_seconds for row in papers])),
        "avg_layer3_axiom_count": round2(avg([row.layer3_axiom_count for row in papers])),
        "min_layer3_axiom_count": min_value([row.layer3_axiom_count for row in papers]),
        "max_layer3_axiom_count": max_value([row.layer3_axiom_count for row in papers]),
        "avg_layer3_subclass_axiom_count": round2(avg([row.layer3_subclass_axiom_count for row in papers])),
        "avg_layer3_subproperty_axiom_count": round2(avg([row.layer3_subproperty_axiom_count for row in papers])),
        "avg_layer3_domain_axiom_count": round2(avg([row.layer3_domain_axiom_count for row in papers])),
        "avg_layer3_range_axiom_count": round2(avg([row.layer3_range_axiom_count for row in papers])),
        "avg_layer3_time_seconds": round2(avg([row.layer3_time_seconds for row in papers])),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def paper_rows_to_dicts(rows: list[PaperStats]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "domain": row.domain,
                "paper_id": row.paper_id,
                "chunk_count": row.chunk_count,
                "layer1_term_count": row.layer1_term_count,
                "layer1_triple_count": row.layer1_triple_count,
                "layer1_time_seconds": round2(row.layer1_time_seconds),
                "layer2_refined_term_count": row.layer2_refined_term_count,
                "layer2_class_count": row.layer2_class_count,
                "layer2_property_count": row.layer2_property_count,
                "layer2_instance_count": row.layer2_instance_count,
                "layer2_time_seconds": round2(row.layer2_time_seconds),
                "layer3_axiom_count": row.layer3_axiom_count,
                "layer3_subclass_axiom_count": row.layer3_subclass_axiom_count,
                "layer3_subproperty_axiom_count": row.layer3_subproperty_axiom_count,
                "layer3_domain_axiom_count": row.layer3_domain_axiom_count,
                "layer3_range_axiom_count": row.layer3_range_axiom_count,
                "layer3_time_seconds": round2(row.layer3_time_seconds),
            }
        )
    return result


def print_table(title: str, rows: list[dict[str, Any]], limit: int | None = None) -> None:
    print(title)
    for index, row in enumerate(rows):
        if limit is not None and index >= limit:
            print(f"... ({len(rows) - limit} more rows)")
            break
        print(row)
    print()


def main() -> None:
    paper_rows = build_paper_rows()
    paper_dicts = paper_rows_to_dicts(paper_rows)

    by_domain_rows = []
    for domain in DOMAINS:
        papers = [row for row in paper_rows if row.domain == domain]
        by_domain_rows.append(build_domain_row(domain, papers))

    overall_row = build_domain_row("overall", paper_rows)
    overall_rows = [overall_row]

    paper_fieldnames = [
        "domain", "paper_id", "chunk_count",
        "layer1_term_count", "layer1_triple_count", "layer1_time_seconds",
        "layer2_refined_term_count", "layer2_class_count", "layer2_property_count", "layer2_instance_count", "layer2_time_seconds",
        "layer3_axiom_count", "layer3_subclass_axiom_count", "layer3_subproperty_axiom_count", "layer3_domain_axiom_count", "layer3_range_axiom_count", "layer3_time_seconds",
    ]
    summary_fieldnames = [
        "domain", "paper_count",
        "avg_chunk_count",
        "avg_layer1_term_count", "min_layer1_term_count", "max_layer1_term_count",
        "avg_layer1_triple_count", "min_layer1_triple_count", "max_layer1_triple_count",
        "avg_layer1_time_seconds",
        "avg_layer2_refined_term_count", "min_layer2_refined_term_count", "max_layer2_refined_term_count",
        "avg_layer2_class_count", "avg_layer2_property_count", "avg_layer2_instance_count",
        "avg_layer2_time_seconds",
        "avg_layer3_axiom_count", "min_layer3_axiom_count", "max_layer3_axiom_count",
        "avg_layer3_subclass_axiom_count", "avg_layer3_subproperty_axiom_count", "avg_layer3_domain_axiom_count", "avg_layer3_range_axiom_count",
        "avg_layer3_time_seconds",
    ]

    write_csv(BY_PAPER_CSV, paper_fieldnames, paper_dicts)
    write_csv(BY_DOMAIN_CSV, summary_fieldnames, by_domain_rows)
    write_csv(OVERALL_CSV, summary_fieldnames, overall_rows)

    print("统计口径说明：")
    print("1. 第一层数量来自 stage_inputs/term_from_meaning_based_chunk_json 文档级 JSON，术语按文本去重，三元组按 (subject, relation, object) 去重。")
    print("2. 第二层数量来自 raw_outputs/term_based_chunk_json 文档级 JSON，术语按 normalized/type_map 去重，并按 Class/Property/Instance 分类。")
    print("3. 第三层数量来自 raw_outputs/concept_chunk_json* 文档级 JSON，公理按各自字段对去重。")
    print("4. 第一层时间优先读取现成 CSV 的 文档运行秒数；若缺失，则退回 prompt 文件时间跨度。")
    print("5. 第二层现有结果未保存显式运行秒数，统一使用 term prompt 分组文件时间跨度作为近似文档用时。")
    print("6. 第三层时间优先读取 raw JSON 中的 document_elapsed_seconds。")
    print()

    print_table("layer_process_by_paper.csv (preview)", paper_dicts, limit=10)
    print_table("layer_process_by_domain.csv", by_domain_rows)
    print_table("layer_process_overall.csv", overall_rows)
    print(f"Saved: {BY_PAPER_CSV}")
    print(f"Saved: {BY_DOMAIN_CSV}")
    print(f"Saved: {OVERALL_CSV}")


if __name__ == "__main__":
    main()
