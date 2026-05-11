from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

import networkx as nx


CHAPTER4_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES: list[tuple[str, Path]] = [
    ("baseline", CHAPTER4_DIR / "exp_4_5" / "baseline_result"),
    ("three_layer", CHAPTER4_DIR / "exp_4_5" / "chunk_result"),
]
DEFAULT_OUTPUT_DIR = CHAPTER4_DIR / "exp_4_5" / "tables"
BY_DOMAIN_FILENAME = "semantic_content_by_domain.csv"
SUMMARY_FILENAME = "semantic_content_summary.csv"
VALID_AXIOM_TYPES = {"subClassOf", "subPropertyOf"}

SUBCLASS_PATTERNS = [
    re.compile(r"SubClassOf\s*\(\s*(?P<subject>.+?)\s+(?P<object>.+?)\s*\)", re.IGNORECASE),
    re.compile(r"(?P<subject>[^\s()]+)\s+subClassOf\s+(?P<object>[^\s()]+)", re.IGNORECASE),
]
SUBPROPERTY_PATTERNS = [
    re.compile(r"SubPropertyOf\s*\(\s*(?P<subject>.+?)\s+(?P<object>.+?)\s*\)", re.IGNORECASE),
    re.compile(r"(?P<subject>[^\s()]+)\s+subPropertyOf\s+(?P<object>[^\s()]+)", re.IGNORECASE),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate hierarchy complexity and semantic content from ontology results."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for output CSV files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="METHOD=PATH",
        help=(
            "Optional input source mapping. Example: "
            "--source baseline=/path/to/baseline_result "
            "--source three_layer=/path/to/chunk_result"
        ),
    )
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.strip("`'\" \t\r\n,.;")


def infer_domain(path: Path) -> str:
    for part in path.parts:
        lowered = part.lower()
        if lowered in {"medical", "geography", "transportation"}:
            return lowered
    return "unknown"


def parse_source_args(source_args: list[str]) -> list[tuple[str, Path]]:
    if not source_args:
        return DEFAULT_SOURCES
    sources: list[tuple[str, Path]] = []
    for item in source_args:
        if "=" not in item:
            raise ValueError(f"Invalid --source value: {item!r}. Expected METHOD=PATH.")
        method, raw_path = item.split("=", 1)
        method = normalize_text(method)
        path = Path(raw_path).expanduser().resolve()
        sources.append((method, path))
    return sources


def parse_axiom_text(axiom_text: str, axiom_type: str) -> tuple[str, str] | None:
    text = normalize_text(axiom_text)
    if not text:
        return None
    patterns = SUBCLASS_PATTERNS if axiom_type == "subClassOf" else SUBPROPERTY_PATTERNS
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        subject = normalize_text(match.group("subject"))
        obj = normalize_text(match.group("object"))
        if subject and obj and subject != obj:
            return subject, obj
    return None


def extract_subject_object(record: dict[str, Any], axiom_type: str) -> tuple[str, str] | None:
    candidate_pairs = [
        ("subject", "object"),
        ("sub", "super"),
        ("subjectTerm", "objectTerm"),
        ("child", "parent"),
    ]
    for left_key, right_key in candidate_pairs:
        subject = normalize_text(record.get(left_key))
        obj = normalize_text(record.get(right_key))
        if subject and obj and subject != obj:
            return subject, obj

    parsed = parse_axiom_text(
        record.get("axiom_text", "") or record.get("axiomText", ""),
        axiom_type,
    )
    if parsed:
        return parsed
    return None


def yield_records_from_payload(
    payload: Any,
    default_method: str,
    path: Path,
) -> Iterable[tuple[str, str, str, str, str]]:
    domain = infer_domain(path)

    if isinstance(payload, dict):
        method = normalize_text(payload.get("method")) or default_method
        domain = normalize_text(payload.get("domain")) or domain

        if any(key in payload for key in ("subClassOf", "subPropertyOf")):
            for axiom_type in ("subClassOf", "subPropertyOf"):
                for item in payload.get(axiom_type, []) or []:
                    if not isinstance(item, dict):
                        continue
                    pair = extract_subject_object(item, axiom_type)
                    if pair:
                        yield method, domain, axiom_type, pair[0], pair[1]
            return

        payload = [payload]

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            method = normalize_text(item.get("method")) or default_method
            item_domain = normalize_text(item.get("domain")) or domain
            axiom_type = normalize_text(
                item.get("axiom_type") or item.get("axiomType") or item.get("type")
            )
            if axiom_type not in VALID_AXIOM_TYPES:
                for fallback_type in ("subClassOf", "subPropertyOf"):
                    parsed = parse_axiom_text(
                        item.get("axiom_text", "") or item.get("axiomText", ""),
                        fallback_type,
                    )
                    if parsed:
                        yield method, item_domain, fallback_type, parsed[0], parsed[1]
                        break
                continue

            pair = extract_subject_object(item, axiom_type)
            if pair:
                yield method, item_domain, axiom_type, pair[0], pair[1]


def load_records_from_file(
    path: Path,
    default_method: str,
) -> Iterable[tuple[str, str, str, str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        yield from yield_records_from_payload(payload, default_method, path)
        return

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        yield from yield_records_from_payload(rows, default_method, path)


def collect_edges(
    sources: list[tuple[str, Path]],
) -> dict[tuple[str, str], dict[str, set[tuple[str, str]]]]:
    grouped: dict[tuple[str, str], dict[str, set[tuple[str, str]]]] = defaultdict(
        lambda: {"subClassOf": set(), "subPropertyOf": set()}
    )

    for default_method, root in sources:
        if not root.exists():
            raise FileNotFoundError(f"Input source does not exist: {root}")
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".json", ".csv"}:
                continue
            for method, domain, axiom_type, subject, obj in load_records_from_file(path, default_method):
                subject = normalize_text(subject)
                obj = normalize_text(obj)
                if not subject or not obj or subject == obj:
                    continue
                grouped[(method, domain)][axiom_type].add((subject, obj))
    return grouped


def merge_by_method(
    grouped: dict[tuple[str, str], dict[str, set[tuple[str, str]]]]
) -> dict[str, dict[str, set[tuple[str, str]]]]:
    merged: dict[str, dict[str, set[tuple[str, str]]]] = defaultdict(
        lambda: {"subClassOf": set(), "subPropertyOf": set()}
    )
    for (method, _domain), axiom_map in grouped.items():
        merged[method]["subClassOf"].update(axiom_map["subClassOf"])
        merged[method]["subPropertyOf"].update(axiom_map["subPropertyOf"])
    return merged


def build_graph(edges: set[tuple[str, str]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_edges_from(edge for edge in edges if edge[0] != edge[1])
    return graph


def build_condensed_graph(graph: nx.DiGraph) -> tuple[nx.DiGraph, dict[Any, int]]:
    if graph.number_of_nodes() == 0:
        return nx.DiGraph(), {}

    sccs = list(nx.strongly_connected_components(graph))
    component_of: dict[Any, int] = {}
    for index, component in enumerate(sccs):
        for node in component:
            component_of[node] = index

    condensed = nx.DiGraph()
    condensed.add_nodes_from(range(len(sccs)))
    for source, target in graph.edges():
        source_component = component_of[source]
        target_component = component_of[target]
        if source_component != target_component:
            condensed.add_edge(source_component, target_component)
    return condensed, {index: len(component) for index, component in enumerate(sccs)}


def compute_depth_metrics(graph: nx.DiGraph) -> tuple[int, float]:
    if graph.number_of_nodes() == 0:
        return 0, 0.0

    # Hierarchy complexity follows the "parent -> child" direction.
    # Input ontology edges are stored as "sub -> super", so reverse them here
    # while keeping node and direct-edge counts unchanged.
    hierarchy_graph = graph.reverse(copy=True)

    condensed, component_sizes = build_condensed_graph(hierarchy_graph)
    if condensed.number_of_nodes() == 0:
        return 0, 0.0

    roots = [node for node, indegree in condensed.in_degree() if indegree == 0]
    if not roots:
        roots = list(condensed.nodes())

    shortest_depth: dict[int, int] = {}
    queue: deque[tuple[int, int]] = deque((root, 0) for root in roots)
    while queue:
        node, depth = queue.popleft()
        if node in shortest_depth and shortest_depth[node] <= depth:
            continue
        shortest_depth[node] = depth
        for child in condensed.successors(node):
            next_depth = depth + 1
            if shortest_depth.get(child, 10**9) > next_depth:
                queue.append((child, next_depth))

    longest_depth = {node: (-10**9) for node in condensed.nodes()}
    for root in roots:
        longest_depth[root] = 0
    for node in nx.topological_sort(condensed):
        if longest_depth[node] < 0:
            continue
        for child in condensed.successors(node):
            longest_depth[child] = max(longest_depth[child], longest_depth[node] + 1)

    leaves = [node for node, outdegree in condensed.out_degree() if outdegree == 0]
    max_depth = max((longest_depth[node] for node in leaves), default=0)

    weighted_total = sum(
        shortest_depth.get(node, 0) * component_sizes[node]
        for node in condensed.nodes()
    )
    total_nodes = sum(component_sizes.values())
    avg_depth = weighted_total / total_nodes if total_nodes else 0.0
    return max_depth, avg_depth


def compute_semantic_content(graph: nx.DiGraph) -> int:
    if graph.number_of_nodes() == 0:
        return 0
    closure = nx.transitive_closure(graph)
    return sum(1 for source, target in closure.edges() if source != target)


def compute_relation_metrics(edges: set[tuple[str, str]]) -> dict[str, Any]:
    graph = build_graph(edges)
    max_depth, avg_depth = compute_depth_metrics(graph)
    return {
        "node_count": graph.number_of_nodes(),
        "direct_edge_count": graph.number_of_edges(),
        "max_depth": max_depth,
        "avg_depth": avg_depth,
        "semantic_content": compute_semantic_content(graph),
    }


def compute_row(method: str, domain: str, axiom_map: dict[str, set[tuple[str, str]]]) -> dict[str, Any]:
    subclass_metrics = compute_relation_metrics(axiom_map["subClassOf"])
    subproperty_metrics = compute_relation_metrics(axiom_map["subPropertyOf"])
    return {
        "method": method,
        "domain": domain,
        "class_node_count": subclass_metrics["node_count"],
        "direct_subclass_edge_count": subclass_metrics["direct_edge_count"],
        "class_max_depth": subclass_metrics["max_depth"],
        "class_avg_depth": round(subclass_metrics["avg_depth"], 4),
        "subclass_semantic_content": subclass_metrics["semantic_content"],
        "property_node_count": subproperty_metrics["node_count"],
        "direct_subproperty_edge_count": subproperty_metrics["direct_edge_count"],
        "property_max_depth": subproperty_metrics["max_depth"],
        "property_avg_depth": round(subproperty_metrics["avg_depth"], 4),
        "subproperty_semantic_content": subproperty_metrics["semantic_content"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_rows(title: str, rows: list[dict[str, Any]]) -> None:
    print(title)
    for row in rows:
        print(
            f"method={row['method']:<12} "
            f"domain={row['domain']:<15} "
            f"class_nodes={row['class_node_count']:<5} "
            f"subclass_edges={row['direct_subclass_edge_count']:<5} "
            f"class_max_depth={row['class_max_depth']:<2} "
            f"class_avg_depth={row['class_avg_depth']:<7} "
            f"subclass_semantic={row['subclass_semantic_content']:<6} "
            f"property_nodes={row['property_node_count']:<5} "
            f"subproperty_edges={row['direct_subproperty_edge_count']:<5} "
            f"property_max_depth={row['property_max_depth']:<2} "
            f"property_avg_depth={row['property_avg_depth']:<7} "
            f"subproperty_semantic={row['subproperty_semantic_content']:<6}"
        )
    print()


def main() -> None:
    args = parse_args()
    sources = parse_source_args(args.source)
    grouped = collect_edges(sources)

    by_domain_rows = [
        compute_row(method, domain, axiom_map)
        for (method, domain), axiom_map in sorted(grouped.items())
    ]

    by_method_grouped = merge_by_method(grouped)
    summary_rows = [
        compute_row(method, "all", axiom_map)
        for method, axiom_map in sorted(by_method_grouped.items())
    ]

    fieldnames = [
        "method",
        "domain",
        "class_node_count",
        "direct_subclass_edge_count",
        "class_max_depth",
        "class_avg_depth",
        "subclass_semantic_content",
        "property_node_count",
        "direct_subproperty_edge_count",
        "property_max_depth",
        "property_avg_depth",
        "subproperty_semantic_content",
    ]

    by_domain_path = args.output_dir / BY_DOMAIN_FILENAME
    summary_path = args.output_dir / SUMMARY_FILENAME
    write_csv(by_domain_path, by_domain_rows, fieldnames)
    write_csv(summary_path, summary_rows, fieldnames)

    print(f"Saved by-domain results to: {by_domain_path}")
    print(f"Saved summary results to: {summary_path}")
    print()
    print("Rules:")
    print("1. Only subClassOf and subPropertyOf axioms are used.")
    print("2. Direct edges are deduplicated, and self-loops are removed before graph construction.")
    print("3. Node counts are the numbers of graph nodes participating in at least one remaining edge.")
    print("4. Hierarchy depth is computed on the same deduplicated graph. Small cycles are condensed into SCCs before depth calculation.")
    print("5. Semantic content is the transitive-closure edge count after removing self-loops.")
    print("6. Isolated nodes are never added separately, so they do not affect semantic content.")
    print()
    print_rows("By domain:", by_domain_rows)
    print_rows("By method summary:", summary_rows)


if __name__ == "__main__":
    main()
