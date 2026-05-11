from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
from openai import OpenAI
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from tqdm import tqdm


# =========================
# Manual Config
# 直接改这里，不需要命令行参数
# =========================
MODEL_NAME = "gpt-5-mini"
OPENAI_API_KEY = "sk-dusmrPQZswbeAR4EejXA67BozRsyvREZs9myIINYgVaKiEnI"
OPENAI_BASE_URL = "https://api2.aigcbest.top/v1"

INPUT_CSV = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/data/nell/raw/nell_rdfs_eval_dataset.csv")
OUTPUT_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/results/openai_results/nell_results")

MAX_TOKENS = 8192
TEMPERATURE = 0.0
SLEEP_SECONDS = 0.5
MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 1.5

TEST_MODE = False
TEST_SIZE = 10


MODEL_OUTPUT_DIR = OUTPUT_DIR / "gpt_5_mini_instruction_enhanced"
RAW_OUTPUT_DIR = MODEL_OUTPUT_DIR / "raw_outputs"
METRICS_DIR = MODEL_OUTPUT_DIR / "metrics"
ERROR_CASES_DIR = MODEL_OUTPUT_DIR / "error_cases"

RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)
ERROR_CASES_DIR.mkdir(parents=True, exist_ok=True)


def build_prompt(axiom_text: str) -> str:
    return f"""
你是一位本体学习专家。请根据给定的RDFS语义规则，对本体公理的正确性进行判断。

任务说明：
RDFS本体公理描述类和属性之间的语义关系，主要包括以下四类：

1）子类关系（subClassOf）：
如果类A是类B的子类，则A的所有实例都属于B。

2）子属性关系（subPropertyOf）：
如果属性P是属性Q的子属性，则任意通过P关联的资源对也必须满足Q关系。

3）定义域（domain）：
如果属性P的定义域为类C，则“使用该属性的主体必须属于类C”。

4）值域（range）：
如果属性P的值域为类C，则“该属性的客体必须属于类C”。

判断步骤：
请按照以下步骤进行推理：
（1）识别该公理的类型（subClassOf / subPropertyOf / domain / range）；
（2）根据对应语义规则，判断该关系是否成立；
（3）结合常识知识，判断是否存在明显语义冲突；
（4）给出最终判断结果。

判断标准：
- 如果该公理符合语义规则且符合常识，则判断为“正确”；
- 如果违反语义规则或明显不符合常识，则判断为“错误”。

公理：
{axiom_text}

请严格按照以下格式输出（必须完全一致，不要添加任何额外内容）：
判断结果：[正确/错误]
解释：[基于语义规则的一句话说明]
""".strip()


def build_fallback_prompt(axiom_text: str) -> str:
    return f"""
你是一位本体学习专家。请判断以下RDFS本体公理是否正确。

公理：
{axiom_text}

你只能输出一行，且必须完全使用以下格式：
判断结果：[正确/错误]
""".strip()


def model_slug(model_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", model_name).strip("_").lower()


def parse_model_label(text: str):
    if not text or not isinstance(text, str):
        return None

    match = re.search(r"判断结果\s*[:：]\s*\[?\s*(正确|错误)\s*\]?", text)
    if match:
        return 1 if match.group(1) == "正确" else 0

    if "判断结果" in text and "正确" in text and "错误" not in text:
        return 1
    if "判断结果" in text and "错误" in text and "正确" not in text:
        return 0

    return None


def safe_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


def save_error_cases(result_df: pd.DataFrame, save_path: Path) -> None:
    error_df = result_df.copy()
    error_df = error_df.dropna(subset=["model_label"])
    error_df["model_label"] = error_df["model_label"].astype(int)
    error_df = error_df[error_df["label"] != error_df["model_label"]]
    error_df.to_csv(save_path, index=False, encoding="utf-8-sig")


def build_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("请先在脚本顶部填写 OPENAI_API_KEY。")

    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**client_kwargs)


def extract_message_text(response) -> str:
    if not response or not getattr(response, "choices", None):
        return ""

    message = response.choices[0].message
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    text_parts.append(str(text_value))
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    text_parts.append(str(text_value))
        return "\n".join(text_parts).strip()

    return str(content or "").strip()


def call_openai_once(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_message_text(response)


def call_openai_with_retry(client: OpenAI, prompt: str) -> tuple[str, str]:
    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            output_text = call_openai_once(client, prompt)
            if output_text:
                return output_text, ""
            last_error = f"empty response on attempt {attempt}"
        except Exception as exc:
            last_error = f"attempt {attempt}: {exc}"

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_SLEEP_SECONDS)

    return "", last_error


def recover_label_with_fallback(client: OpenAI, axiom_text: str) -> tuple[str, int | None, str]:
    fallback_output, fallback_error = call_openai_with_retry(
        client, build_fallback_prompt(axiom_text)
    )
    fallback_label = parse_model_label(fallback_output)

    if fallback_output and fallback_label is not None:
        return fallback_output, fallback_label, ""

    error_msg = "fallback failed"
    if fallback_error:
        error_msg = f"{error_msg}: {fallback_error}"
    return fallback_output, None, error_msg


def load_dataset() -> pd.DataFrame:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"未找到输入数据集文件：{INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    required_columns = {"axiom_type", "axiom_text", "label"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"数据集缺少必要字段: {missing_columns}")

    if "id" not in df.columns:
        df["id"] = [f"sample_{i:04d}" for i in range(1, len(df) + 1)]

    if TEST_MODE:
        df = df.head(TEST_SIZE).copy()
        print(f"[INFO] 当前为测试模式，仅运行前 {len(df)} 条样本。")
    else:
        print(f"[INFO] 当前为正式模式，共运行 {len(df)} 条样本。")

    return df


def print_run_config() -> None:
    print("=== Manual Config ===")
    print(f"MODEL_NAME      : {MODEL_NAME}")
    print(f"OPENAI_BASE_URL : {OPENAI_BASE_URL or '(default)'}")
    print(f"INPUT_CSV       : {INPUT_CSV}")
    print(f"OUTPUT_DIR      : {OUTPUT_DIR}")
    print(f"MODEL_OUTPUT_DIR: {MODEL_OUTPUT_DIR}")
    print(f"MAX_TOKENS      : {MAX_TOKENS}")
    print(f"TEMPERATURE     : {TEMPERATURE}")
    print(f"SLEEP_SECONDS   : {SLEEP_SECONDS}")
    print(f"MAX_RETRIES     : {MAX_RETRIES}")
    print(f"RETRY_SLEEP_SEC : {RETRY_SLEEP_SECONDS}")
    print(f"TEST_MODE       : {TEST_MODE}")
    print(f"TEST_SIZE       : {TEST_SIZE}")
    print()


def main():
    print_run_config()
    client = build_client()
    df = load_dataset()

    results = []
    run_name = model_slug(MODEL_NAME)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Running {MODEL_NAME}"):
        sample_id = row["id"]
        axiom_type = str(row["axiom_type"])
        axiom_text = str(row["axiom_text"])
        true_label = int(row["label"])
        prompt = build_prompt(axiom_text)

        output_text = ""
        pred_label = None
        is_correct = None
        error_msg = ""

        try:
            output_text, retry_error = call_openai_with_retry(client, prompt)
            pred_label = parse_model_label(output_text)

            if not output_text or pred_label is None:
                fallback_output, fallback_label, fallback_error = recover_label_with_fallback(
                    client, axiom_text
                )
                if fallback_output:
                    output_text = fallback_output
                if fallback_label is not None:
                    pred_label = fallback_label
                if retry_error or fallback_error:
                    error_msg = " | ".join(
                        part for part in [retry_error, fallback_error] if part
                    )

            if pred_label is not None:
                is_correct = int(pred_label == true_label)
            elif retry_error and not error_msg:
                error_msg = retry_error
        except Exception as exc:
            error_msg = str(exc)

        results.append(
            {
                "id": sample_id,
                "axiom_type": axiom_type,
                "axiom_text": axiom_text,
                "label": true_label,
                "model_name": MODEL_NAME,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
                "base_url": OPENAI_BASE_URL,
                "model_output": output_text,
                "model_label": pred_label,
                "is_correct": is_correct,
                "error": error_msg,
            }
        )

        time.sleep(SLEEP_SECONDS)

    result_df = pd.DataFrame(results)
    prefix = "test" if TEST_MODE else "full"

    result_csv = RAW_OUTPUT_DIR / f"{prefix}_results.csv"
    overall_csv = METRICS_DIR / f"{prefix}_overall_metrics.csv"
    by_type_csv = METRICS_DIR / f"{prefix}_metrics_by_type.csv"
    by_label_csv = METRICS_DIR / f"{prefix}_metrics_by_label.csv"
    error_csv = ERROR_CASES_DIR / f"{prefix}_error_samples.csv"

    result_df.to_csv(result_csv, index=False, encoding="utf-8-sig")

    eval_df = result_df.dropna(subset=["model_label"]).copy()
    if len(eval_df) == 0:
        print("[WARN] 没有可评估样本，模型输出可能未按格式返回，或请求全部失败。")
        print(f"[INFO] 逐条结果已保存到: {result_csv}")
        return

    eval_df["model_label"] = eval_df["model_label"].astype(int)

    overall_metrics = safe_metrics(eval_df["label"], eval_df["model_label"])
    overall_df = pd.DataFrame(
        [
            {
                "model_name": MODEL_NAME,
                "total_samples": len(result_df),
                "parsed_samples": len(eval_df),
                **overall_metrics,
            }
        ]
    )
    overall_df.to_csv(overall_csv, index=False, encoding="utf-8-sig")

    by_type_rows = []
    for axiom_type, group in eval_df.groupby("axiom_type"):
        metrics = safe_metrics(group["label"], group["model_label"])
        by_type_rows.append({"axiom_type": axiom_type, "samples": len(group), **metrics})
    by_type_df = pd.DataFrame(by_type_rows).sort_values("axiom_type")
    by_type_df.to_csv(by_type_csv, index=False, encoding="utf-8-sig")

    by_label_rows = []
    for label_value, group in eval_df.groupby("label"):
        accuracy = (group["label"] == group["model_label"]).mean()
        by_label_rows.append(
            {
                "label": int(label_value),
                "label_name": "positive" if int(label_value) == 1 else "negative",
                "samples": len(group),
                "accuracy": accuracy,
            }
        )
    by_label_df = pd.DataFrame(by_label_rows).sort_values("label")
    by_label_df.to_csv(by_label_csv, index=False, encoding="utf-8-sig")

    save_error_cases(result_df, error_csv)

    print("\n=== Overall Metrics ===")
    print(overall_df.to_string(index=False))

    print("\n=== Metrics by Axiom Type ===")
    print(by_type_df.to_string(index=False))

    print("\n=== Metrics by Label ===")
    print(by_label_df.to_string(index=False))

    print("\nSaved files:")
    print(result_csv)
    print(overall_csv)
    print(by_type_csv)
    print(by_label_csv)
    print(error_csv)


if __name__ == "__main__":
    main()
