from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3")
INPUT_CSV = BASE_DIR / "results/openai_results/dbpedia_results/dbpedia_experiment_metrics_summary.csv"
OUTPUT_PATH = BASE_DIR / "results/visualizations/comparison_chart_of_different_prompt.png"


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

    model_map = {
        "claude_haiku": "Claude-Haiku-4.5",
        "gpt_5_mini": "GPT-5-mini",
        "qwen_max": "Qwen-Max",
    }

    prompt_map = {
        "basic_prompt": "Basic Prompt",
        "instruction_enhanced_prompt": "Instruction-Enhanced",
        "context_guided_prompt": "Context-Guided",
    }

    model_order = ["claude_haiku", "gpt_5_mini", "qwen_max"]
    prompt_order = ["basic_prompt", "instruction_enhanced_prompt", "context_guided_prompt"]

    df["模型"] = pd.Categorical(df["模型"], categories=model_order, ordered=True)
    df["提示词"] = pd.Categorical(df["提示词"], categories=prompt_order, ordered=True)
    df = df.sort_values(["模型", "提示词"])

    pos_df = df.pivot(index="模型", columns="提示词", values="正例Acc").reindex(model_order)
    neg_df = df.pivot(index="模型", columns="提示词", values="负例Acc").reindex(model_order)
    all_df = df.pivot(index="模型", columns="提示词", values="整体Acc").reindex(model_order)

    fig, axes = plt.subplots(1, 3, figsize=(13, 6.6), dpi=300)

    datasets = [
        ("Positive Example", pos_df),
        ("Negative Example", neg_df),
        ("Overall Example", all_df),
    ]

    colors = ["#6B8BA4", "#A8837E", "#7A9D7C"]
    edge_colors = ["#4F697E", "#8B6C67", "#5C7D5E"]
    x = np.arange(len(model_order))
    width = 0.16

    for ax, (title, data) in zip(axes, datasets):
        for i, prompt in enumerate(prompt_order):
            series = pd.to_numeric(data[prompt], errors="coerce")
            ax.bar(
                x + (i - 1) * width,
                series.values,
                width=width,
                label=prompt_map[prompt],
                color=colors[i],
                edgecolor=edge_colors[i],
                linewidth=0.8,
            )

        ax.set_title(title, fontsize=16, pad=14)
        ax.set_xticks(x)
        ax.set_xticklabels([model_map[m] for m in model_order], rotation=0, fontsize=13)
        ax.set_ylabel("Accuracy", fontsize=14)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#B8BDC6")
        ax.tick_params(axis="y", labelsize=13)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#A7ADB5")
        ax.spines["bottom"].set_color("#A7ADB5")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.03), frameon=False, fontsize=13)

    plt.tight_layout(rect=[0, 0.1, 1, 1])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
