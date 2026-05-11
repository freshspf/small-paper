from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASELINE_CONFIG = "COUNT+DOMAIN+NAMING"
ENTITY_CONFIG = "COUNT+DOMAIN+NAMING+ENTITY"
BAR_COLORS = ["#6B8BA4", "#A8837E"]
BAR_EDGE_COLORS = ["#4F697E", "#8B6C67"]
TYPE_COLOR = "#7A9D7C"
TYPE_EDGE_COLOR = "#5C7D5E"

data = [
    ["Geography", BASELINE_CONFIG, 150, 0.33, 49],
    ["Geography", ENTITY_CONFIG, 150, 0.34, 51],
    ["Medical", BASELINE_CONFIG, 130, 0.85, 110],
    ["Medical", ENTITY_CONFIG, 130, 0.78, 138],
    ["Transportation", BASELINE_CONFIG, 118, 0.33, 39],
    ["Transportation", ENTITY_CONFIG, 118, 0.36, 42],
]

df = pd.DataFrame(
    data,
    columns=["Domain", "Config", "Total_Axioms", "Accuracy_axiom", "N_valid"],
)

type_data = [
    ["Geography", 0.93],
    ["Medical", 0.94],
    ["Transportation", 0.92],
]

df_type = pd.DataFrame(type_data, columns=["Domain", "TypeAccuracy"])

OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/outputs/visualizations/experiment_4_4/entity_switch_comparison_chart.png"
)


def draw_bar(ax: plt.Axes, pivot_df: pd.DataFrame, title: str, ylabel: str) -> None:
    x = np.arange(len(pivot_df.index))
    width = 0.34

    base_values = pivot_df[BASELINE_CONFIG].to_numpy()
    entity_values = pivot_df[ENTITY_CONFIG].to_numpy()

    ax.bar(
        x - width / 2,
        base_values,
        width=width,
        color=BAR_COLORS[0],
        edgecolor=BAR_EDGE_COLORS[0],
        linewidth=0.8,
        label=BASELINE_CONFIG,
    )
    ax.bar(
        x + width / 2,
        entity_values,
        width=width,
        color=BAR_COLORS[1],
        edgecolor=BAR_EDGE_COLORS[1],
        linewidth=0.8,
        label=ENTITY_CONFIG,
    )

    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index.tolist(), rotation=0, fontsize=11)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")
    ax.legend(frameon=False, fontsize=10)


def draw_single_bar(ax: plt.Axes, type_df: pd.DataFrame, title: str, ylabel: str) -> None:
    x = np.arange(len(type_df["Domain"]))
    values = type_df["TypeAccuracy"].to_numpy()

    ax.bar(
        x,
        values,
        width=0.6,
        color=TYPE_COLOR,
        edgecolor=TYPE_EDGE_COLOR,
        linewidth=0.8,
    )

    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(type_df["Domain"].tolist(), rotation=0, fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")


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


def main() -> None:
    configure_matplotlib()

    total_df = df.pivot(index="Domain", columns="Config", values="Total_Axioms")
    accuracy_df = df.pivot(index="Domain", columns="Config", values="Accuracy_axiom")
    valid_df = df.pivot(index="Domain", columns="Config", values="N_valid")

    fig, axes = plt.subplots(1, 4, figsize=(20, 5.2), dpi=300)

    draw_bar(axes[0], total_df, "Axiom Count Comparison", "Count")
    draw_bar(axes[1], accuracy_df, "Accuracy Comparison", "Accuracy")
    draw_bar(axes[2], valid_df, "Valid Axiom Comparison", "Valid Count")
    draw_single_bar(axes[3], df_type, "Type Accuracy", "Type Accuracy")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
