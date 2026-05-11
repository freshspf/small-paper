import csv
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUTS_DIR = BASE_DIR / "outputs"
ANNOTATIONS_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"

BASELINE_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "baseline_chunk_json" / "medical"
THREE_STAGE_DIR = OUTPUTS_DIR / "raw_outputs" / "experiment_4_5" / "claude_sonnet_4_6" / "concept_chunk_json" / "medical"
OUTPUT_CSV = ANNOTATIONS_DIR / "final_ontology_annotation_comparison_medical.csv"

MODEL_NAME = "Claude-Sonnet-4.6"
METHOD_MAP = {
    "baseline": BASELINE_DIR,
    "three_stage": THREE_STAGE_DIR,
}

CSV_HEADERS = [
    "模型",
    "领域",
    "文档ID",
    "方法",
    "公理类型",
    "公理序号",
    "subject",
    "predicate",
    "object",
    "axiom_text",
    "是否正确",
    "错误类型",
    "备注",
    "来源文件",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows_for_result(method: str, path: Path) -> list[dict[str, str]]:
    data = load_json(path)
    doc_id = str(data.get("doc_id", "")).strip() or path.stem
    domain = str(data.get("domain", "")).strip() or path.parent.name
    rows: list[dict[str, str]] = []
    axiom_index = 1

    def append_row(axiom_type: str, subject: str, predicate: str, object_value: str) -> None:
        nonlocal axiom_index
        rows.append(
            {
                "模型": MODEL_NAME,
                "领域": domain,
                "文档ID": doc_id,
                "方法": method,
                "公理类型": axiom_type,
                "公理序号": str(axiom_index),
                "subject": subject,
                "predicate": predicate,
                "object": object_value,
                "axiom_text": f"{subject} {predicate} {object_value}".strip(),
                "是否正确": "",
                "错误类型": "",
                "备注": "",
                "来源文件": str(path),
            }
        )
        axiom_index += 1

    for class_name in data.get("classes", []):
        class_text = str(class_name).strip()
        if class_text:
            append_row("Class", class_text, "declare_class", "")

    for property_name in data.get("properties", []):
        property_text = str(property_name).strip()
        if property_text:
            append_row("Property", property_text, "declare_property", "")

    for item in data.get("subClassOf", []):
        append_row(
            "subClassOf",
            str(item.get("sub", "")).strip(),
            "subClassOf",
            str(item.get("super", "")).strip(),
        )

    for item in data.get("subPropertyOf", []):
        append_row(
            "subPropertyOf",
            str(item.get("sub", "")).strip(),
            "subPropertyOf",
            str(item.get("super", "")).strip(),
        )

    for item in data.get("domain_axioms", []):
        append_row(
            "domain",
            str(item.get("property", "")).strip(),
            "domain",
            str(item.get("class", "")).strip(),
        )

    for item in data.get("range_axioms", []):
        append_row(
            "range",
            str(item.get("property", "")).strip(),
            "range",
            str(item.get("class", "")).strip(),
        )

    return rows


def main() -> None:
    all_rows: list[dict[str, str]] = []

    for method, directory in METHOD_MAP.items():
        if not directory.exists():
            raise FileNotFoundError(f"未找到目录: {directory}")

        for path in sorted(directory.glob("*.json")):
            all_rows.extend(build_rows_for_result(method, path))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
