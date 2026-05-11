from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


data = [
    ["Geography", "COUNT+DOMAIN", 159, 49, 0.31, 49],
    ["Geography", "COUNT+DOMAIN+NAMING", 150, 49, 0.33, 49],
    ["Medical", "COUNT+DOMAIN", 128, 110, 0.86, 110],
    ["Medical", "COUNT+DOMAIN+NAMING", 130, 110, 0.85, 110],
    ["Transportation", "COUNT+DOMAIN", 122, 39, 0.32, 39],
    ["Transportation", "COUNT+DOMAIN+NAMING", 118, 39, 0.33, 39],
]

df = pd.DataFrame(
    data,
    columns=["Domain", "Config", "Total_Axioms", "Correct_Axioms", "Accuracy_axiom", "N_valid"],
)

OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/outputs/visualizations/experiment_4_4/naming_switch_comparison_chart.png"
)


def draw_bar(ax: plt.Axes, pivot_df: pd.DataFrame, title: str, ylabel: str) -> None:
    x = np.arange(len(pivot_df.index))
    width = 0.34

    base_values = pivot_df["COUNT+DOMAIN"].to_numpy()
    naming_values = pivot_df["COUNT+DOMAIN+NAMING"].to_numpy()

    colors = ["#6B8BA4", "#A8837E"]
    edge_colors = ["#4F697E", "#8B6C67"]

    ax.bar(
        x - width / 2,
        base_values,
        width=width,
        color=colors[0],
        edgecolor=edge_colors[0],
        linewidth=0.8,
        label="COUNT+DOMAIN",
    )
    ax.bar(
        x + width / 2,
        naming_values,
        width=width,
        color=colors[1],
        edgecolor=edge_colors[1],
        linewidth=0.8,
        label="COUNT+DOMAIN+NAMING",
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

    total_df = df.pivot(index="Domain", columns="Config", values="Total_Axioms")
    accuracy_df = df.pivot(index="Domain", columns="Config", values="Accuracy_axiom")
    valid_df = df.pivot(index="Domain", columns="Config", values="N_valid")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), dpi=300)

    draw_bar(axes[0], total_df, "Axiom Count Comparison", "Count")
    draw_bar(axes[1], accuracy_df, "Accuracy Comparison", "Accuracy")
    draw_bar(axes[2], valid_df, "Valid Axiom Comparison", "Valid Count")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
