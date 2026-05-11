from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_PATH = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/visualizations/fig3_6_model_axiom_f1_comparison.png")


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
    x = np.arange(len(axiom_types))

    gpt_f1 = [0.9070, 0.8083, 0.6983, 0.8140]
    claude_f1 = [0.8951, 0.6938, 0.6524, 0.7767]
    qwen_f1 = [0.9138, 0.4763, 0.4698, 0.7374]

    colors = {
        "GPT-5-mini": "#6B8BA4",
        "Claude-Haiku-4.5": "#A8837E",
        "Qwen-Max": "#7A9D7C",
    }

    plt.figure(figsize=(10, 6))

    plt.plot(x, gpt_f1, marker="o", markersize=7, linewidth=2.2, color=colors["GPT-5-mini"], label="GPT-5-mini")
    plt.plot(
        x,
        claude_f1,
        marker="s",
        markersize=7,
        linewidth=2.2,
        color=colors["Claude-Haiku-4.5"],
        label="Claude-Haiku-4.5",
    )
    plt.plot(x, qwen_f1, marker="^", markersize=7, linewidth=2.2, color=colors["Qwen-Max"], label="Qwen-Max")

    plt.xticks(x, axiom_types, fontsize=11)
    plt.yticks(fontsize=11)
    plt.ylim(0.4, 1.0)
    plt.xlabel("Axiom Type", fontsize=12)
    plt.ylabel("F1 Score", fontsize=12)
    plt.title("Model-Level F1 Comparison Across Axiom Types", fontsize=13, pad=12)
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
