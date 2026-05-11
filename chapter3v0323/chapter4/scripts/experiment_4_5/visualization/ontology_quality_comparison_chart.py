from pathlib import Path

import csv
import matplotlib.pyplot as plt
import numpy as np


INPUT_CSV = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/data/annotations/experiment_4_5/claude_sonnet_4_6/ontology_quality_plot_table_2604_04357v1.csv"
)
OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/results/visualizations/ontology_quality_comparison_2604_04357v1.png"
)


def configure_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = [
        "PingFang SC",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def load_rows() -> list[dict[str, str]]:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    configure_matplotlib()
    rows = load_rows()
    if not rows:
        raise ValueError(f"未读取到绘图数据: {INPUT_CSV}")

    method_map = {
        "baseline": "Baseline",
        "three_stage": "Three-Stage",
    }
    methods = [method_map.get(row["方法"], row["方法"]) for row in rows]

    keep_rate = [float(row["建议保留率"]) for row in rows]
    naming_rate = [float(row["命名规范率"]) for row in rows]
    property_rate = [float(row["Property保留率"]) for row in rows]
    subclass_rate = [float(row["subClassOf保留率"]) for row in rows]
    structure_rate = [float(row["Structure保留率"]) for row in rows]
    explicit_count = [int(row["明确支持数"]) for row in rows]
    reasonable_count = [int(row["合理扩展数"]) for row in rows]
    delete_count = [int(row["建议删除数"]) for row in rows]

    x = np.arange(len(methods))
    width = 0.22

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.4), dpi=300)

    # 1. Overall quality
    ax = axes[0]
    ax.bar(x - width / 2, keep_rate, width=width, color=colors[0], edgecolor=edge_colors[0], linewidth=0.8, label="Keep Rate")
    ax.bar(x + width / 2, naming_rate, width=width, color=colors[1], edgecolor=edge_colors[1], linewidth=0.8, label="Naming Rate")
    ax.set_title("Overall Quality", fontsize=12, pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Ratio", fontsize=11)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    # 2. Structural quality
    ax = axes[1]
    ax.bar(x - width, property_rate, width=width, color=colors[0], edgecolor=edge_colors[0], linewidth=0.8, label="Property")
    ax.bar(x, subclass_rate, width=width, color=colors[1], edgecolor=edge_colors[1], linewidth=0.8, label="subClassOf")
    ax.bar(x + width, structure_rate, width=width, color=colors[2], edgecolor=edge_colors[2], linewidth=0.8, label="Structure")
    ax.set_title("Structural Quality", fontsize=12, pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    # 3. Support composition
    ax = axes[2]
    ax.bar(x - width, explicit_count, width=width, color=colors[0], edgecolor=edge_colors[0], linewidth=0.8, label="Explicit")
    ax.bar(x, reasonable_count, width=width, color=colors[1], edgecolor=edge_colors[1], linewidth=0.8, label="Reasonable")
    ax.bar(x + width, delete_count, width=width, color=colors[2], edgecolor=edge_colors[2], linewidth=0.8, label="Delete")
    ax.set_title("Support Composition", fontsize=12, pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=11)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    plt.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
