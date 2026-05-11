from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/exp_4_5")
OUTPUT_DIR = BASE_DIR / "picture_result/chunk_baseline"
OUTPUT_PATH = OUTPUT_DIR / "baseline_comparison_of_axiom_accuracy.png"

DOMAINS = ["Geography", "Medical", "Transportation"]
BASELINE = [0.69, 0.66, 0.82]
THREE_LAYER = [0.41, 0.34, 0.51]


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

    x = np.arange(len(DOMAINS))
    width = 0.34

    fig, ax = plt.subplots(figsize=(9.8, 5.8), dpi=300)

    baseline_bars = ax.bar(
        x - width / 2,
        BASELINE,
        width=width,
        label="Baseline",
        color="#8FA8A1",
        edgecolor="#4F5B58",
        linewidth=0.8,
    )
    three_layer_bars = ax.bar(
        x + width / 2,
        THREE_LAYER,
        width=width,
        label="Three-layer",
        color="#D8C3A5",
        edgecolor="#8C7B6A",
        linewidth=0.8,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("Accuracy", fontsize=13)
    ax.tick_params(axis="x", labelsize=12)
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

    upper = max(BASELINE) * 1.18
    ax.set_ylim(0, upper)

    for bars in (baseline_bars, three_layer_bars):
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + upper * 0.02,
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
