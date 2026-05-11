from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_PATH = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/visualizations/fig3_5_axiom_type_comparison.png")


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

    axiom_types = ["subClassOf", "subPropertyOf", "domain", "range"]
    accuracy = [0.8761, 0.8614, 0.7516, 0.7383]
    precision = [0.9305, 0.9228, 0.9496, 0.9478]
    recall = [0.8127, 0.7915, 0.5064, 0.4857]
    f1 = [0.8668, 0.8520, 0.6592, 0.6420]

    x = np.arange(len(axiom_types))

    colors = {
        "Accuracy": "#6B8BA4",
        "Precision": "#A8837E",
        "Recall": "#7A9D7C",
        "F1": "#B39B6B",
    }

    plt.figure(figsize=(10, 6))

    plt.plot(x, accuracy, marker="o", markersize=7, linewidth=2.2, color=colors["Accuracy"], label="Accuracy")
    plt.plot(x, precision, marker="s", markersize=7, linewidth=2.2, color=colors["Precision"], label="Precision")
    plt.plot(x, recall, marker="^", markersize=7, linewidth=2.2, color=colors["Recall"], label="Recall")
    plt.plot(x, f1, marker="D", markersize=7, linewidth=2.2, color=colors["F1"], label="F1")

    plt.xticks(x, axiom_types, fontsize=11)
    plt.yticks(fontsize=11)
    plt.ylim(0.4, 1.0)
    plt.xlabel("Axiom Type", fontsize=12)
    plt.ylabel("Metric Value", fontsize=12)
    plt.title("Performance Across Different Axiom Types", fontsize=13, pad=12)
    plt.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
    plt.legend(fontsize=10, frameon=False)

    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")

    plt.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
