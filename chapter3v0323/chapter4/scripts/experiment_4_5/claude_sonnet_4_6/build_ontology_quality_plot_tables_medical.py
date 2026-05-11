import csv
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
ANNOTATION_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"

INPUT_CSV = ANNOTATION_DIR / "ontology_quality_annotation_medical_assistant.csv"
METHOD_SUMMARY_CSV = ANNOTATION_DIR / "ontology_quality_plot_table_medical_method_summary.csv"
TYPE_BREAKDOWN_CSV = ANNOTATION_DIR / "ontology_quality_plot_table_medical_axiom_type_breakdown.csv"


def pct(num: int, den: int) -> str:
    if den == 0:
        return "0.00"
    return f"{num / den:.2f}"


def main() -> None:
    method_total = Counter()
    method_explicit = Counter()
    method_reasonable = Counter()
    method_naming = Counter()
    method_keep = Counter()

    type_total: dict[tuple[str, str], int] = defaultdict(int)
    type_explicit: dict[tuple[str, str], int] = defaultdict(int)
    type_reasonable: dict[tuple[str, str], int] = defaultdict(int)
    type_naming: dict[tuple[str, str], int] = defaultdict(int)
    type_keep: dict[tuple[str, str], int] = defaultdict(int)

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row["方法"].strip()
            axiom_type = row["公理类型"].strip()
            key = (method, axiom_type)

            method_total[method] += 1
            type_total[key] += 1

            if row["是否被原文明确支持"].strip() == "是":
                method_explicit[method] += 1
                type_explicit[key] += 1
            if row["是否为合理扩展"].strip() == "是":
                method_reasonable[method] += 1
                type_reasonable[key] += 1
            if row["命名是否规范"].strip() == "是":
                method_naming[method] += 1
                type_naming[key] += 1
            if row["是否建议保留"].strip() == "是":
                method_keep[method] += 1
                type_keep[key] += 1

    method_rows = []
    for method in sorted(method_total):
        total = method_total[method]
        explicit = method_explicit[method]
        reasonable = method_reasonable[method]
        naming = method_naming[method]
        keep = method_keep[method]
        method_rows.append(
            {
                "方法": method,
                "总公理数": str(total),
                "原文明确支持数": str(explicit),
                "原文明确支持率": pct(explicit, total),
                "合理扩展数": str(reasonable),
                "合理扩展率": pct(reasonable, total),
                "命名规范数": str(naming),
                "命名规范率": pct(naming, total),
                "建议保留数": str(keep),
                "建议保留率": pct(keep, total),
            }
        )

    type_rows = []
    for method, axiom_type in sorted(type_total):
        total = type_total[(method, axiom_type)]
        explicit = type_explicit[(method, axiom_type)]
        reasonable = type_reasonable[(method, axiom_type)]
        naming = type_naming[(method, axiom_type)]
        keep = type_keep[(method, axiom_type)]
        type_rows.append(
            {
                "方法": method,
                "公理类型": axiom_type,
                "总数": str(total),
                "原文明确支持数": str(explicit),
                "原文明确支持率": pct(explicit, total),
                "合理扩展数": str(reasonable),
                "合理扩展率": pct(reasonable, total),
                "命名规范数": str(naming),
                "命名规范率": pct(naming, total),
                "建议保留数": str(keep),
                "建议保留率": pct(keep, total),
            }
        )

    with METHOD_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "方法",
                "总公理数",
                "原文明确支持数",
                "原文明确支持率",
                "合理扩展数",
                "合理扩展率",
                "命名规范数",
                "命名规范率",
                "建议保留数",
                "建议保留率",
            ],
        )
        writer.writeheader()
        writer.writerows(method_rows)

    with TYPE_BREAKDOWN_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "方法",
                "公理类型",
                "总数",
                "原文明确支持数",
                "原文明确支持率",
                "合理扩展数",
                "合理扩展率",
                "命名规范数",
                "命名规范率",
                "建议保留数",
                "建议保留率",
            ],
        )
        writer.writeheader()
        writer.writerows(type_rows)

    print(f"Wrote method summary: {METHOD_SUMMARY_CSV}")
    print(f"Wrote type breakdown: {TYPE_BREAKDOWN_CSV}")


if __name__ == "__main__":
    main()
