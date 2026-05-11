from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3")
OUTPUT_DIR = BASE_DIR / "results/visualizations"
OUTPUT_PATH = OUTPUT_DIR / "comparison_chart_of_accuracy_rate_and_illusion_rate.png"

MODELS = [
    "ERNIE 4.5",
    "Qwen Max",
    "Claude Sonnet 4.6",
    "GPT-5.4",
    "Grok 4",
    "DeepSeek R1",
    "Gemini 2.5 Pro",
    "Claude Haiku 4.5",
    "Doubao Pro",
    "GPT-5 Mini",
    "Llama 3.1 70B",
]

ACCURACY = [0.8750, 0.6875, 0.6750, 0.6750, 0.6625, 0.6625, 0.5750, 0.5625, 0.5375, 0.5250, 0.5125]
HALLUCINATION = [0.10, 0.20, 0.2750, 0.3250, 0.2875, 0.2125, 0.3375, 0.3125, 0.40, 0.40, 0.3625]


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

    accuracy_bars = ax.bar(
        x - width / 2,
        ACCURACY,
        width=width,
        label="Explanation Accuracy",
        color="#8FA8A1",
        edgecolor="#4F5B58",
        linewidth=0.8,
    )
    hallucination_bars = ax.bar(
        x + width / 2,
        HALLUCINATION,
        width=width,
        label="Hallucination Rate",
        color="#D8C3A5",
        edgecolor="#8C7B6A",
        linewidth=0.8,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=28, ha="right")
    ax.set_ylim(0, 1.0)
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

    for bars in (accuracy_bars, hallucination_bars):
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
