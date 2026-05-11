import re
from pathlib import Path
from collections import defaultdict

import pandas as pd


# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

ONTOLOGY_CSV = BASE_DIR / "data" / "nell" / "raw" / "nell_rdfs_eval_dataset.csv"
# 注意：这里不是直接重新读远程 ontology.gz，而是先从你已经构建好的样本集提取 URI，
# 再用原始 ontology 文件补上下文信息。
NELL_ONTOLOGY_CSV_GZ = "http://rtw.ml.cmu.edu/resources/results/08m/NELL.08m.1115.ontology.csv.gz"

OUTPUT_DIR = BASE_DIR / "data" / "nell" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "nell_uri_context_mapping.csv"


# =========================
# Utils
# =========================
def safe_str(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def short_name(value: str) -> str:
    value = safe_str(value)
    if not value:
        return ""
    if ":" in value:
        return value.split(":")[-1]
    if "/" in value:
        return value.rstrip("/").split("/")[-1]
    return value


def normalize_text(text: str, max_len: int = 240) -> str:
    text = safe_str(text)
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text


def norm_predicate(value: str) -> str:
    value = safe_str(value).strip().lower()
    value = value.strip('"').strip("'")
    return value


def infer_kind(uri: str) -> str:
    uri = safe_str(uri)
    if uri.startswith("concept:"):
        return "Class"
    if uri.startswith("relation:"):
        return "Property"
    return "Unknown"


def make_fallback_description(name: str, kind: str) -> str:
    if kind == "Property":
        return f"{name} is a property in the NELL knowledge base."
    if kind == "Class":
        return f"{name} is a class in the NELL knowledge base."
    return f"{name} is an entity in the NELL knowledge base."


def extract_unique_uris(df: pd.DataFrame) -> list[str]:
    uris = set()
    for col in ["subject", "object"]:
        if col in df.columns:
            vals = df[col].dropna().astype(str).tolist()
            uris.update(v for v in vals if v.strip())
    return sorted(uris)


# =========================
# Load NELL ontology
# =========================
def load_nell_ontology() -> pd.DataFrame:
    print(f"[INFO] Loading NELL ontology from: {NELL_ONTOLOGY_CSV_GZ}")

    df = pd.read_csv(
        NELL_ONTOLOGY_CSV_GZ,
        compression="gzip",
        sep="\t",
        header=None,
        names=["subject", "predicate", "object"],
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )

    df = df.fillna("")

    # 去掉表头行
    df = df[
        ~(
            df["subject"].astype(str).str.strip().str.lower().eq("entity")
            & df["predicate"].astype(str).str.strip().str.lower().eq("relation")
            & df["object"].astype(str).str.strip().str.lower().eq("value")
        )
    ].copy()

    df = df[
        (df["subject"].astype(str).str.strip() != "")
        & (df["predicate"].astype(str).str.strip() != "")
        & (df["object"].astype(str).str.strip() != "")
    ].copy()

    df = df.reset_index(drop=True)

    print(f"[INFO] Loaded ontology rows: {len(df)}")
    return df


# =========================
# Build metadata index
# =========================
def build_metadata_index(df_onto: pd.DataFrame) -> dict:
    """
    为每个 subject 聚合 ontology 元信息：
    - description
    - humanformat
    - generalizations
    """
    meta = defaultdict(lambda: {
        "description": [],
        "humanformat": [],
        "generalizations": [],
        "domain": [],
        "range": [],
    })

    for _, row in df_onto.iterrows():
        subj = safe_str(row["subject"])
        pred = norm_predicate(row["predicate"])
        obj = safe_str(row["object"])

        if not subj or not pred or not obj:
            continue

        if pred == "description":
            meta[subj]["description"].append(obj)
        elif pred == "humanformat":
            meta[subj]["humanformat"].append(obj)
        elif pred == "generalizations":
            meta[subj]["generalizations"].append(obj)
        elif pred == "domain":
            meta[subj]["domain"].append(obj)
        elif pred == "range":
            meta[subj]["range"].append(obj)

    return meta


def choose_description(uri: str, info: dict) -> tuple[str, str]:
    """
    返回:
    - description
    - status
    """
    descriptions = [normalize_text(x) for x in info.get("description", []) if normalize_text(x)]
    if descriptions:
        return descriptions[0], "ok"

    humanformats = [normalize_text(x) for x in info.get("humanformat", []) if normalize_text(x)]
    if humanformats:
        return humanformats[0], "partial"

    kind = infer_kind(uri)
    return make_fallback_description(short_name(uri), kind), "fallback"


def build_extra_info(info: dict) -> str:
    parts = []

    gens = [short_name(x) for x in info.get("generalizations", [])[:3]]
    if gens:
        parts.append(f"generalizations: {', '.join(gens)}")

    domains = [short_name(x) for x in info.get("domain", [])[:3]]
    if domains:
        parts.append(f"domain: {', '.join(domains)}")

    ranges = [short_name(x) for x in info.get("range", [])[:3]]
    if ranges:
        parts.append(f"range: {', '.join(ranges)}")

    return normalize_text(" | ".join(parts), max_len=180)


# =========================
# Main
# =========================
def main():
    print("=== Build NELL Context Mapping ===")
    print(f"ONTOLOGY_CSV: {ONTOLOGY_CSV}")
    print(f"OUTPUT_CSV  : {OUTPUT_CSV}")

    if not ONTOLOGY_CSV.exists():
        raise FileNotFoundError(f"未找到构建好的 NELL 数据集：{ONTOLOGY_CSV}")

    dataset_df = pd.read_csv(ONTOLOGY_CSV)
    required_cols = {"subject", "object"}
    missing_cols = required_cols - set(dataset_df.columns)
    if missing_cols:
        raise ValueError(f"NELL 数据集缺少必要字段: {missing_cols}")

    uri_list = extract_unique_uris(dataset_df)
    print(f"[INFO] Unique URI count in dataset: {len(uri_list)}")

    df_onto = load_nell_ontology()
    meta_index = build_metadata_index(df_onto)

    rows = []
    for idx, uri in enumerate(uri_list, start=1):
        if idx % 50 == 0 or idx == 1 or idx == len(uri_list):
            print(f"[INFO] Processing {idx}/{len(uri_list)}")

        info = meta_index.get(uri, {
            "description": [],
            "humanformat": [],
            "generalizations": [],
            "domain": [],
            "range": [],
        })

        desc, status = choose_description(uri, info)
        extra_info = build_extra_info(info)

        rows.append({
            "uri": uri,
            "name": short_name(uri),
            "kind": infer_kind(uri),
            "label_en": short_name(uri),
            "description": desc,
            "extra_info": extra_info,
            "source": "NELL_ontology",
            "status": status,
        })

    mapping_df = pd.DataFrame(rows).drop_duplicates(subset=["uri"]).reset_index(drop=True)
    mapping_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n=== Summary ===")
    print(mapping_df["status"].value_counts(dropna=False).to_string())

    print("\n=== Kind Distribution ===")
    print(mapping_df["kind"].value_counts(dropna=False).to_string())

    print(f"\n[INFO] 输出文件已保存：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()