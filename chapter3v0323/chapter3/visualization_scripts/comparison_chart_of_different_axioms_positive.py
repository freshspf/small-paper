from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3")
INPUT_CSV = BASE_DIR / "results/openai_results/context_guided_axiom_model_positive_accuracy_average_summary.csv"
OUTPUT_PATH = BASE_DIR / "results/visualizations/comparison_chart_of_different_axioms_positive.png"


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

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    axiom_order = ["subClassOf", "subPropertyOf", "domain", "range"]
    model_order = ["claude-haiku", "gpt-5-mini", "qwen-max"]
    model_labels = ["Claude-Haiku-4.5", "GPT-5-mini", "Qwen-Max"]

    df["公理类型"] = pd.Categorical(df["公理类型"], categories=axiom_order, ordered=True)
    df["模型"] = pd.Categorical(df["模型"], categories=model_order, ordered=True)
    df = df.sort_values(["公理类型", "模型"])

    pivot_df = df.pivot(index="公理类型", columns="模型", values="Accuracy").reindex(axiom_order)

    x = np.arange(len(axiom_order))
    width = 0.25

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]

    plt.figure(figsize=(8.5, 5.2), dpi=300)

    for i, model in enumerate(model_order):
        plt.bar(
            x + (i - 1) * width,
            pd.to_numeric(pivot_df[model], errors="coerce").values,
            width=width,
            label=model_labels[i],
            color=colors[i],
            edgecolor=edge_colors[i],
            linewidth=0.8,
        )

    plt.xticks(x, axiom_order, fontsize=11)
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
