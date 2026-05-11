from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "results" / "visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "fig3_4_dataset_comparison.png"


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

    datasets = ["DBpedia", "YAGO", "NELL"]
    accuracy = [0.8073, 0.7444, 0.8475]
    precision = [0.9296, 0.9051, 0.9492]
    recall = [0.6809, 0.5344, 0.7111]
    f1 = [0.7693, 0.6626, 0.7630]

    x = np.arange(len(datasets))
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
    ax.set_xticklabels(datasets, fontsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Dataset", fontsize=12)
    ax.set_ylabel("Metric Value", fontsize=12)
    ax.set_title("Overall Performance Across Different Datasets", fontsize=13)
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
