from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3")
OUTPUT_DIR = BASE_DIR / "results/visualizations"
OUTPUT_PATH = OUTPUT_DIR / "stability_assessment_comparison_chart.png"

MODELS = [
    "Claude Sonnet 4.6",
    "Qwen Max",
    "GPT-5.4",
    "Gemini 2.5 Pro",
    "DeepSeek R1",
    "Llama 3.1 70B",
    "GPT-5 Mini",
    "Doubao Pro",
    "ERNIE 4.5",
    "Claude Haiku 4.5",
    "Grok 4",
]

HARD_CONSISTENCY = [0.63, 0.60, 0.59, 0.57, 0.52, 0.51, 0.48, 0.46, 0.43, 0.40, 0.39]
SOFT_CONSISTENCY = [0.06, 0.07, 0.08, 0.09, 0.10, 0.10, 0.11, 0.11, 0.12, 0.12, 0.13]


def configure_font() -> None:
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
    configure_font()

    x = np.arange(len(MODELS))
    width = 0.34

    fig, ax = plt.subplots(figsize=(13.5, 6.8), dpi=300)

    hard_bars = ax.bar(
        x - width / 2,
        HARD_CONSISTENCY,
        width=width,
        label="Hard Consistency",
        color="#8FA8A1",
        edgecolor="#4F5B58",
        linewidth=0.8,
    )
    soft_bars = ax.bar(
        x + width / 2,
        SOFT_CONSISTENCY,
        width=width,
        label="Soft Consistency",
        color="#D8C3A5",
        edgecolor="#8C7B6A",
        linewidth=0.8,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=28, ha="right")
    ax.set_ylim(0, 0.72)
    ax.set_ylabel("Score", fontsize=13)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35, color="#B8BDC6")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.28),
        ncol=2,
        frameon=False,
        fontsize=11,
    )

    for bars in (hard_bars, soft_bars):
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.012,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
                color="#444444",
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, 0.12, 1, 1])
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
