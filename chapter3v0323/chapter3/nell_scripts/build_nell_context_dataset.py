import re
from pathlib import Path
from typing import Optional

import pandas as pd


# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DATASET_CSV = BASE_DIR / "data" / "nell" / "raw" / "nell_rdfs_eval_dataset.csv"
INPUT_MAPPING_CSV = BASE_DIR / "data" / "nell" / "processed" / "nell_uri_context_mapping.csv"

OUTPUT_DIR = BASE_DIR / "data" / "nell" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DATASET_CSV = OUTPUT_DIR / "nell_rdfs_eval_dataset_with_context.csv"


# =========================
# Utils
# =========================
def safe_str(value: Optional[object]) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_text(text: str, max_len: int = 240) -> str:
    text = safe_str(text)
    if not text:
        return ""

    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text


def short_name(value: str) -> str:
    value = safe_str(value)
    if not value:
        return ""
    if ":" in value:
        return value.split(":")[-1]
    if "/" in value:
        return value.rstrip("/").split("/")[-1]
    return value


def choose_description(row: dict) -> str:
    """
    description > label_en > name > fallback
    """
    for key in ["description", "label_en", "name"]:
        value = normalize_text(row.get(key, ""))
        if value:
            return value
    return "No additional description is available."


def infer_kind_from_uri(uri: str) -> str:
    uri = safe_str(uri)
    if uri.startswith("concept:"):
        return "Class"
    if uri.startswith("relation:"):
        return "Property"
    return "Unknown"


def build_single_context_card(row: dict) -> str:
    name = safe_str(row.get("name", "")) or "Unknown"
    kind = safe_str(row.get("kind", "")) or "Unknown"
    desc = choose_description(row)
    extra_info = normalize_text(row.get("extra_info", ""), max_len=180)

    lines = [
        f"- 名称：{name}",
        f"- 类型：{kind}",
        f"- 简介：{desc}",
    ]

    if extra_info:
        lines.append(f"- 补充信息：{extra_info}")

    return "\n".join(lines)


def build_fallback_row(uri: str) -> dict:
    name = short_name(uri)
    kind = infer_kind_from_uri(uri)
    if kind == "Property":
        desc = f"{name} is a property in the NELL knowledge base."
    elif kind == "Class":
        desc = f"{name} is a class in the NELL knowledge base."
    else:
        desc = f"{name} is an entity in the NELL knowledge base."

    return {
        "uri": uri,
        "name": name,
        "kind": kind,
        "label_en": name,
        "description": desc,
        "extra_info": "",
        "source": "fallback",
        "status": "fallback",
    }


def load_mapping_dict(mapping_df: pd.DataFrame) -> dict:
    mapping_dict = {}
    for _, row in mapping_df.iterrows():
        uri = safe_str(row.get("uri", ""))
        if not uri:
            continue

        mapping_dict[uri] = {
            "uri": uri,
            "name": safe_str(row.get("name", "")),
            "kind": safe_str(row.get("kind", "")) or "Unknown",
            "label_en": safe_str(row.get("label_en", "")),
            "description": safe_str(row.get("description", "")),
            "extra_info": safe_str(row.get("extra_info", "")),
            "source": safe_str(row.get("source", "")),
            "status": safe_str(row.get("status", "")),
        }

    return mapping_dict


def build_context_info(subject_row: dict, object_row: dict) -> tuple[str, str, str]:
    subject_context = build_single_context_card(subject_row)
    object_context = build_single_context_card(object_row)

    context_info = (
        "背景知识：\n"
        "条目1：\n"
        f"{subject_context}\n\n"
        "条目2：\n"
        f"{object_context}"
    )

    return subject_context, object_context, context_info


# =========================
# Main
# =========================
def main():
    print("=== Build NELL Context Dataset ===")
    print(f"INPUT_DATASET_CSV: {INPUT_DATASET_CSV}")
    print(f"INPUT_MAPPING_CSV: {INPUT_MAPPING_CSV}")
    print(f"OUTPUT_DATASET_CSV: {OUTPUT_DATASET_CSV}")

    if not INPUT_DATASET_CSV.exists():
        raise FileNotFoundError(f"未找到原始数据集：{INPUT_DATASET_CSV}")

    if not INPUT_MAPPING_CSV.exists():
        raise FileNotFoundError(f"未找到 URI 映射文件：{INPUT_MAPPING_CSV}")

    dataset_df = pd.read_csv(INPUT_DATASET_CSV)
    mapping_df = pd.read_csv(INPUT_MAPPING_CSV)

    required_dataset_cols = {"subject", "object", "axiom_type", "axiom_text", "label"}
    missing_dataset_cols = required_dataset_cols - set(dataset_df.columns)
    if missing_dataset_cols:
        raise ValueError(f"原始数据集缺少必要字段: {missing_dataset_cols}")

    required_mapping_cols = {"uri", "name", "kind"}
    missing_mapping_cols = required_mapping_cols - set(mapping_df.columns)
    if missing_mapping_cols:
        raise ValueError(f"映射文件缺少必要字段: {missing_mapping_cols}")

    mapping_dict = load_mapping_dict(mapping_df)

    subject_context_list = []
    object_context_list = []
    context_info_list = []

    subject_hit = 0
    object_hit = 0

    for _, row in dataset_df.iterrows():
        subject_uri = safe_str(row.get("subject", ""))
        object_uri = safe_str(row.get("object", ""))

        subject_row = mapping_dict.get(subject_uri)
        object_row = mapping_dict.get(object_uri)

        if subject_row is not None:
            subject_hit += 1
        else:
            subject_row = build_fallback_row(subject_uri)

        if object_row is not None:
            object_hit += 1
        else:
            object_row = build_fallback_row(object_uri)

        subject_context, object_context, context_info = build_context_info(subject_row, object_row)

        subject_context_list.append(subject_context)
        object_context_list.append(object_context)
        context_info_list.append(context_info)

    output_df = dataset_df.copy()
    output_df["subject_context"] = subject_context_list
    output_df["object_context"] = object_context_list
    output_df["context_info"] = context_info_list

    output_df.to_csv(OUTPUT_DATASET_CSV, index=False, encoding="utf-8-sig")

    print("\n=== Summary ===")
    print(f"总样本数: {len(output_df)}")
    print(f"subject 匹配成功数: {subject_hit} / {len(output_df)}")
    print(f"object 匹配成功数 : {object_hit} / {len(output_df)}")
    print(f"输出文件已保存: {OUTPUT_DATASET_CSV}")

    print("\n=== Preview: context_info (first 2 rows) ===")
    for i in range(min(2, len(output_df))):
        print(f"\n--- Sample {i + 1} ---")
        print(output_df.iloc[i]["context_info"])


if __name__ == "__main__":
    main()