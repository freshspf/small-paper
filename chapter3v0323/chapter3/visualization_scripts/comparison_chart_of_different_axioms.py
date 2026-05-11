from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


OUTPUT_PATH = Path(
    "/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/visualizations/comparison_chart_of_different_axioms.png"
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
        "Axiom": ["subClassOf", "subPropertyOf", "domain", "range"],
        "Claude-haiku-4-5": [0.93, 0.78, 0.79, 0.84],
        "GPT-5-mini": [0.95, 0.80, 0.79, 0.82],
        "Qwen-max": [0.95, 0.81, 0.81, 0.88],
    }

    df = pd.DataFrame(data)

    x = np.arange(len(df["Axiom"]))
    width = 0.25

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]
    model_labels = ["Claude-Haiku-4.5", "GPT-5-mini", "Qwen-Max"]
    columns = ["Claude-haiku-4-5", "GPT-5-mini", "Qwen-max"]

    plt.figure(figsize=(8.5, 5.2), dpi=300)

    for i, column in enumerate(columns):
        plt.bar(
            x + (i - 1) * width,
            df[column].values,
            width=width,
            label=model_labels[i],
            color=colors[i],
            edgecolor=edge_colors[i],
            linewidth=0.8,
        )

    plt.xticks(x, df["Axiom"], fontsize=11)
    plt.yticks(fontsize=11)
    plt.ylabel("Accuracy", fontsize=11)
    plt.ylim(0, 1.05)
    plt.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    plt.legend(loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=3, frameon=False, fontsize=10)

    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")

    plt.tight_layout(rect=[0, 0.22, 1, 1])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
