from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/visualizations/comparison_char_of_different_models.png"
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


def main() -> None:
    configure_matplotlib()

    models = ["Claude-Haiku-4.5", "GPT-5-mini", "Qwen-Max"]
    pos = [0.73, 0.75, 0.74]
    neg = [0.94, 0.93, 0.98]
    overall = [0.84, 0.84, 0.86]

    x = np.arange(len(models))
    width = 0.6

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), dpi=300)
    datasets = [
        ("Positive Accuracy", pos),
        ("Negative Accuracy", neg),
        ("Overall Accuracy", overall),
    ]

    for ax, (title, values) in zip(axes, datasets):
        ax.bar(x, values, width=width, color=colors, edgecolor=edge_colors, linewidth=0.8)
        ax.set_title(title, fontsize=12, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=0, fontsize=11)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#A7ADB5")
        ax.spines["bottom"].set_color("#A7ADB5")

    axes[0].set_ylabel("Accuracy", fontsize=11)

    plt.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
