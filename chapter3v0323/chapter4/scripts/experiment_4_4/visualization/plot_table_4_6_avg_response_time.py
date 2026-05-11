from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "outputs" / "visualizations" / "experiment_4_4"
OUTPUT_PATH = OUTPUT_DIR / "table_4_6_avg_response_time.png"


CONFIGS = ["P0", "P1", "P2", "P3", "P4"]
MEDICAL = [18.6, 20.4, 21.7, 23.1, 24.8]
GEOGRAPHY = [17.9, 19.6, 20.9, 22.4, 24.1]
TRANSPORTATION = [18.2, 19.9, 21.2, 22.7, 24.3]
AVERAGE = [18.2, 20.0, 21.3, 22.7, 24.4]


COLORS = {
    "medical": "#6B8BA4",
    "geography": "#A8837E",
    "transportation": "#7A9D7C",
    "average": "#D8C09B",
}

EDGE_COLORS = {
    "medical": "#4F697E",
    "geography": "#8B6C67",
    "transportation": "#5C7D5E",
    "average": "#9A8568",
}


def configure_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = [
        "Arial Unicode MS",
        "PingFang SC",
        "Hiragino Sans GB",
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def add_value_labels(ax: plt.Axes, bars) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.18,
            f"{height:.1f}",
            ha="center",
            va="bottom",
            fontsize=11,
            color="#4B5563",
        )


def main() -> None:
    configure_matplotlib()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    x = np.arange(len(CONFIGS))
    width = 0.22

    fig, ax = plt.subplots(figsize=(11.5, 7.0), dpi=300)

    bars_medical = ax.bar(
        x - width,
        MEDICAL,
        width=width,
        color=COLORS["medical"],
        edgecolor=EDGE_COLORS["medical"],
        linewidth=1.2,
        label="Medical",
    )
    bars_geography = ax.bar(
        x,
        GEOGRAPHY,
        width=width,
        color=COLORS["geography"],
        edgecolor=EDGE_COLORS["geography"],
        linewidth=1.2,
        label="Geography",
    )
    bars_transportation = ax.bar(
        x + width,
        TRANSPORTATION,
        width=width,
        color=COLORS["transportation"],
        edgecolor=EDGE_COLORS["transportation"],
        linewidth=1.2,
        label="Transportation",
    )

    avg_line, = ax.plot(
        x,
        AVERAGE,
        color=COLORS["average"],
        marker="o",
        markersize=7,
        linewidth=2.2,
        markeredgecolor=EDGE_COLORS["average"],
        label="Average Response Time",
        zorder=3,
    )

    add_value_labels(ax, bars_medical)
    add_value_labels(ax, bars_geography)
    add_value_labels(ax, bars_transportation)

    for xi, value in zip(x, AVERAGE):
        ax.text(
            xi,
            value + 0.45,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=11,
            color=EDGE_COLORS["average"],
        )

    ax.set_xticks(x)
    ax.set_xticklabels(CONFIGS, fontsize=13)
    ax.set_ylabel("Average Response Time (s)", fontsize=15)
    ax.set_ylim(0, 28)

    ax.grid(axis="y", linestyle="--", linewidth=1, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A7ADB5")
    ax.spines["bottom"].set_color("#A7ADB5")
    ax.tick_params(axis="y", labelsize=13)

    handles = [bars_medical, bars_geography, bars_transportation, avg_line]
    labels = ["Medical", "Geography", "Transportation", "Average Response Time"]
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        frameon=False,
        fontsize=13,
        ncol=4,
    )

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(OUTPUT_PATH, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
