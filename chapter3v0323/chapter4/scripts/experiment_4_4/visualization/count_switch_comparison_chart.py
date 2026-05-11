from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


data = [
    ["Geography", "OFF", 95, 21, 0.22, 21],
    ["Geography", "ON", 171, 31, 0.18, 31],
    ["Medical", "OFF", 91, 49, 0.54, 49],
    ["Medical", "ON", 140, 122, 0.87, 122],
    ["Transportation", "OFF", 92, 60, 0.65, 60],
    ["Transportation", "ON", 147, 44, 0.30, 44],
]

df = pd.DataFrame(
    data,
    columns=["Domain", "Config", "Total", "Correct", "Accuracy", "N_valid"],
)

OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/outputs/visualizations/experiment_4_4/count_switch_comparison_chart.png"
)


def draw_bar(ax: plt.Axes, pivot_df: pd.DataFrame, title: str, ylabel: str) -> None:
    x = np.arange(len(pivot_df.index))
    width = 0.34

    off_values = pivot_df["OFF"].to_numpy()
    on_values = pivot_df["ON"].to_numpy()

    colors = ["#6B8BA4", "#A8837E"]
    edge_colors = ["#4F697E", "#8B6C67"]

    ax.bar(
        x - width / 2,
        off_values,
        width=width,
        color=colors[0],
        edgecolor=edge_colors[0],
        linewidth=0.8,
        label="OFF",
    )
    ax.bar(
        x + width / 2,
        on_values,
        width=width,
        color=colors[1],
        edgecolor=edge_colors[1],
        linewidth=0.8,
        label="ON",
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

    total_df = df.pivot(index="Domain", columns="Config", values="Total")
    valid_df = df.pivot(index="Domain", columns="Config", values="N_valid")
    accuracy_df = df.pivot(index="Domain", columns="Config", values="Accuracy")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), dpi=300)

    draw_bar(axes[0], total_df, "Axiom Count Comparison", "Count")
    draw_bar(axes[1], valid_df, "Valid Axiom Comparison", "Valid Count")
    draw_bar(axes[2], accuracy_df, "Accuracy Comparison", "Accuracy")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
