from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/visualizations/comparison_chart_of_different_dataset.png"
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

    data = {
        "Dataset": ["DBpedia", "YAGO", "NELL"],
        "Claude-haiku-4-5_pos": [0.82, 0.55, 0.83],
        "Claude-haiku-4-5_neg": [0.86, 0.97, 1.00],
        "Claude-haiku-4-5_all": [0.84, 0.76, 0.92],
        "GPT-5-mini_pos": [0.86, 0.50, 0.88],
        "GPT-5-mini_neg": [0.81, 0.99, 0.99],
        "GPT-5-mini_all": [0.84, 0.75, 0.94],
        "Qwen-max_pos": [0.76, 0.51, 0.96],
        "Qwen-max_neg": [0.97, 0.99, 0.99],
        "Qwen-max_all": [0.87, 0.75, 0.97],
    }

    df = pd.DataFrame(data)

    datasets = df["Dataset"]
    x = np.arange(len(datasets))
    width = 0.16

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]
    model_labels = ["Claude-Haiku-4.5", "GPT-5-mini", "Qwen-Max"]

    fig, axes = plt.subplots(1, 3, figsize=(13, 6.6), dpi=300)

    datasets_to_plot = [
        ("Positive Example", ["Claude-haiku-4-5_pos", "GPT-5-mini_pos", "Qwen-max_pos"]),
        ("Negative Example", ["Claude-haiku-4-5_neg", "GPT-5-mini_neg", "Qwen-max_neg"]),
        ("Overall Example", ["Claude-haiku-4-5_all", "GPT-5-mini_all", "Qwen-max_all"]),
    ]

    for ax, (title, columns) in zip(axes, datasets_to_plot):
        for i, column in enumerate(columns):
            ax.bar(
                x + (i - 1) * width,
                df[column].values,
                width=width,
                label=model_labels[i],
                color=colors[i],
                edgecolor=edge_colors[i],
                linewidth=0.8,
            )

        ax.set_title(title, fontsize=16, pad=14)
        ax.set_xticks(x)
        ax.set_xticklabels(datasets, fontsize=13)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
        ax.tick_params(axis="y", labelsize=13)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#A7ADB5")
        ax.spines["bottom"].set_color("#A7ADB5")

    axes[0].set_ylabel("Accuracy", fontsize=14)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.03), frameon=False, fontsize=13)

    plt.tight_layout(rect=[0, 0.1, 1, 1])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
