from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3")
INPUT_CSV = BASE_DIR / "results/openai_results/hard_case_results/hard_case_overall_metrics_summary.csv"
OUTPUT_PATH = BASE_DIR / "results/visualizations/hard_case_accuracy_comparison.png"


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


def simplify_model_name(name: str) -> str:
    mapping = {
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": "DeepSeek R1",
        "Doubao-pro-128k": "Doubao Pro",
        "ernie-4.5-turbo-128k": "ERNIE 4.5",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "gpt-5.4": "GPT-5.4",
        "gpt-5-mini": "GPT-5 Mini",
        "grok-4": "Grok 4",
        "llama-3.1-70b": "Llama 3.1 70B",
        "qwen-max-0125": "Qwen Max",
    }
    return mapping.get(name, name)


def main() -> None:
    configure_font()

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")
    df = df.sort_values("accuracy", ascending=False).reset_index(drop=True)
    df["display_name"] = df["model_name"].map(simplify_model_name)

    fig, ax = plt.subplots(figsize=(13.5, 6.8), dpi=300)

    bars = ax.bar(
        df["display_name"],
        df["accuracy"],
        width=0.58,
        color="#8FA8A1",
        edgecolor="#4F5B58",
        linewidth=0.8,
    )

    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Accuracy", fontsize=13)
    ax.tick_params(axis="x", labelsize=11, rotation=28)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35, color="#B8BDC6")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")

    for bar, value in zip(bars, df["accuracy"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.012,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#444444",
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved figure to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
