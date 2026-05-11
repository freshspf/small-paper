import csv
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
ANNOTATION_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_5" / "claude_sonnet_4_6"

INPUT_CSV = ANNOTATION_DIR / "ontology_quality_annotation_medical_assistant.csv"
METHOD_SUMMARY_CSV = ANNOTATION_DIR / "ontology_quality_plot_table_medical_fair_method_summary.csv"
TYPE_BREAKDOWN_CSV = ANNOTATION_DIR / "ontology_quality_plot_table_medical_fair_axiom_type_breakdown.csv"


def pct(num: int, den: int) -> str:
    if den == 0:
        return "0.00"
    return f"{num / den:.2f}"


def main() -> None:
    method_stats = defaultdict(Counter)
    type_stats = defaultdict(Counter)

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row["方法"].strip()
            axiom_type = row["公理类型"].strip()
            key = (method, axiom_type)

            explicit = row["是否被原文明确支持"].strip() == "是"
            reasonable = row["是否为合理扩展"].strip() == "是"
            naming = row["命名是否规范"].strip() == "是"
            keep = row["是否建议保留"].strip() == "是"
            acceptable = explicit or (reasonable and keep)
            extension_keep = (not explicit) and reasonable and keep

            for bucket in (method_stats[method], type_stats[key]):
                bucket["总公理数"] += 1
                if explicit:
                    bucket["原文明确支持数"] += 1
                if reasonable:
                    bucket["合理扩展数"] += 1
                if naming:
                    bucket["命名规范数"] += 1
                if keep:
                    bucket["建议保留数"] += 1
                if acceptable:
                    bucket["可接受公理数"] += 1
                if extension_keep:
                    bucket["扩展保留数"] += 1

    method_rows = []
    for method in sorted(method_stats):
        stats = method_stats[method]
        total = stats["总公理数"]
        method_rows.append(
            {
                "方法": method,
                "总公理数": str(total),
                "原文明确支持数": str(stats["原文明确支持数"]),
                "原文明确支持率": pct(stats["原文明确支持数"], total),
                "扩展保留数": str(stats["扩展保留数"]),
                "扩展保留率": pct(stats["扩展保留数"], total),
                "可接受公理数": str(stats["可接受公理数"]),
                "可接受率": pct(stats["可接受公理数"], total),
                "建议保留数": str(stats["建议保留数"]),
                "建议保留率": pct(stats["建议保留数"], total),
                "命名规范数": str(stats["命名规范数"]),
                "命名规范率": pct(stats["命名规范数"], total),
            }
        )

    type_rows = []
    for method, axiom_type in sorted(type_stats):
        stats = type_stats[(method, axiom_type)]
        total = stats["总公理数"]
        type_rows.append(
            {
                "方法": method,
                "公理类型": axiom_type,
                "总公理数": str(total),
                "原文明确支持数": str(stats["原文明确支持数"]),
                "原文明确支持率": pct(stats["原文明确支持数"], total),
                "扩展保留数": str(stats["扩展保留数"]),
                "扩展保留率": pct(stats["扩展保留数"], total),
                "可接受公理数": str(stats["可接受公理数"]),
                "可接受率": pct(stats["可接受公理数"], total),
                "建议保留数": str(stats["建议保留数"]),
                "建议保留率": pct(stats["建议保留数"], total),
                "命名规范数": str(stats["命名规范数"]),
                "命名规范率": pct(stats["命名规范数"], total),
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
                "扩展保留数",
                "扩展保留率",
                "可接受公理数",
                "可接受率",
                "建议保留数",
                "建议保留率",
                "命名规范数",
                "命名规范率",
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
                "总公理数",
                "原文明确支持数",
                "原文明确支持率",
                "扩展保留数",
                "扩展保留率",
                "可接受公理数",
                "可接受率",
                "建议保留数",
                "建议保留率",
                "命名规范数",
                "命名规范率",
            ],
        )
        writer.writeheader()
        writer.writerows(type_rows)

    print(f"Wrote fair method summary: {METHOD_SUMMARY_CSV}")
    print(f"Wrote fair type breakdown: {TYPE_BREAKDOWN_CSV}")


if __name__ == "__main__":
    main()
