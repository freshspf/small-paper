from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "results" / "visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "fig3_2_prompt_strategy_comparison.png"


def configure_chinese_font() -> None:
    candidates = [
        "PingFang SC",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti SC",
        "Arial Unicode MS",
    ]
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for font_name in candidates:
        if font_name in available_fonts:
            plt.rcParams["font.sans-serif"] = [font_name]
            break
    else:
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

    plt.rcParams["axes.unicode_minus"] = False


def main() -> None:
    configure_chinese_font()

    prompt_types = ["Basic Prompt", "Instruction-Enhanced", "Context-Guided"]
    accuracy = [0.7819, 0.7719, 0.8454]
    precision = [0.9333, 0.9131, 0.9375]
    recall = [0.6133, 0.6148, 0.7542]
    f1 = [0.7110, 0.6917, 0.8136]

    x = np.arange(len(prompt_types))
    width = 0.2
    colors = ["#8FA8A1", "#A9B7C6", "#C7B8A3", "#B8A0B6"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x - 1.5 * width,
        accuracy,
        width,
        label="Accuracy",
        color=colors[0],
        edgecolor="#4F5B58",
        linewidth=0.8,
    )
    ax.bar(
        x - 0.5 * width,
        precision,
        width,
        label="Precision",
        color=colors[1],
        edgecolor="#55606A",
        linewidth=0.8,
    )
    ax.bar(
        x + 0.5 * width,
        recall,
        width,
        label="Recall",
        color=colors[2],
        edgecolor="#6A5E50",
        linewidth=0.8,
    )
    ax.bar(
        x + 1.5 * width,
        f1,
        width,
        label="F1",
        color=colors[3],
        edgecolor="#665A64",
        linewidth=0.8,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(prompt_types, fontsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Prompt Strategy", fontsize=12)
    ax.set_ylabel("Metric Value", fontsize=12)
    ax.set_title("Overall Performance Across Prompt Strategies", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
