from __future__ import annotations

import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ABSTRACT_DIR = BASE_DIR / "data" / "raw" / "abstracts"
OUTPUT_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_4_manual_full"

MODEL_NAME = "Claude-Sonnet-4.6"
FIELDNAMES = [
    "模型",
    "领域",
    "文档ID",
    "配置轮次",
    "公理序号",
    "subject",
    "relation",
    "object",
    "evidence",
    "是否正确",
    "错误类型",
    "备注",
]

CONFIG_SOURCES = {
    "baseline": [
        BASE_DIR / "outputs" / "raw_outputs" / "count_constraint_ablation" / "claude_sonnet_4.6" / "baseline",
    ],
    "round1": [
        BASE_DIR / "outputs" / "raw_outputs" / "count_constraint_ablation" / "claude_sonnet_4.6" / "round1",
    ],
    "round2": [
        BASE_DIR / "outputs" / "raw_outputs" / "count_constraint_ablation" / "claude_sonnet_4.6" / "round2",
        BASE_DIR / "outputs" / "raw_outputs" / "count_constraint_ablation" / "claude_sonnet_4.6" / "round2_retry_timeout_docs",
    ],
    "round3": [
        BASE_DIR / "outputs" / "raw_outputs" / "naming_constraint_ablation" / "claude_sonnet_4.6" / "round3",
    ],
    "round4": [
        BASE_DIR / "outputs" / "raw_outputs" / "entity_constraint_ablation" / "claude_sonnet_4.6" / "round4",
    ],
}

CONFIG_OUTPUT_NAMES = {
    "baseline": "experiment_4_4_axiom_annotation_baseline.csv",
    "round1": "experiment_4_4_axiom_annotation_count.csv",
    "round2": "experiment_4_4_axiom_annotation_domain.csv",
    "round3": "experiment_4_4_axiom_annotation_naming.csv",
    "round4": "experiment_4_4_axiom_annotation_entity.csv",
}


def build_domain_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for domain_dir in ABSTRACT_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        for txt_file in domain_dir.glob("*.txt"):
            mapping[txt_file.stem] = domain_dir.name
    return mapping


def collect_json_files(config: str) -> list[Path]:
    selected: dict[str, Path] = {}
    for source_dir in CONFIG_SOURCES[config]:
        if not source_dir.exists():
            continue
        for json_path in sorted(source_dir.rglob("*.json")):
            rel_key = json_path.relative_to(source_dir).as_posix()
            selected[rel_key] = json_path
    return [selected[key] for key in sorted(selected)]


def parse_axioms(json_path: Path) -> list[dict[str, str]]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    axioms = data.get("axioms", []) if isinstance(data, dict) else []
    if not isinstance(axioms, list):
        return []
    return axioms


def build_rows(config: str, files: list[Path], domain_map: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for json_path in files:
        paper_id = json_path.stem
        domain = domain_map.get(paper_id, json_path.parent.name)
        axioms = parse_axioms(json_path)
        for index, axiom in enumerate(axioms, start=1):
            chunk = str(axiom.get("chunk", "")).strip()
            evidence = str(axiom.get("evidence", "")).strip()
            if chunk and evidence:
                merged_evidence = f"{chunk}: {evidence}"
            else:
                merged_evidence = evidence or chunk

            rows.append(
                {
                    "模型": MODEL_NAME,
                    "领域": domain,
                    "文档ID": paper_id,
                    "配置轮次": config,
                    "公理序号": str(index),
                    "subject": str(axiom.get("subject", "")).strip(),
                    "relation": str(axiom.get("relation", "")).strip(),
                    "object": str(axiom.get("object", "")).strip(),
                    "evidence": merged_evidence,
                    "是否正确": "",
                    "错误类型": "",
                    "备注": "",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    domain_map = build_domain_map()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for config, output_name in CONFIG_OUTPUT_NAMES.items():
        files = collect_json_files(config)
        rows = build_rows(config, files, domain_map)
        output_path = OUTPUT_DIR / output_name
        write_csv(output_path, rows)
        print(f"{config}: {len(files)} files, {len(rows)} axioms -> {output_path}")


if __name__ == "__main__":
    main()
