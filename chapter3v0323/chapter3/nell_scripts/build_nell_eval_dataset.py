import random
from pathlib import Path

import pandas as pd


# =========================
# Config
# =========================
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# NELL ontology 文件
NELL_ONTOLOGY_CSV_GZ = "http://rtw.ml.cmu.edu/resources/results/08m/NELL.08m.1115.ontology.csv.gz"

# 每类正例数量上限
POSITIVE_CAP_PER_TYPE = 60

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "nell" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "nell" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


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


def norm_predicate(value: str) -> str:
    """
    对 predicate 做归一化：
    - 去空格
    - 小写
    - 去引号
    """
    value = safe_str(value).strip().lower()
    value = value.strip('"').strip("'")
    return value


def cap_positive_df(df: pd.DataFrame, cap: int) -> pd.DataFrame:
    if len(df) <= cap:
        return df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    return df.sample(n=cap, random_state=RANDOM_SEED).reset_index(drop=True)


# =========================
# Load ontology
# =========================
def load_nell_ontology() -> pd.DataFrame:
    print(f"[INFO] Loading NELL ontology from: {NELL_ONTOLOGY_CSV_GZ}")

    # 关键修复：NELL 文件是制表符分隔，不是逗号分隔
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

    # 去掉表头行：Entity\tRelation\tValue
    df = df[
        ~(
            df["subject"].astype(str).str.strip().str.lower().eq("entity")
            & df["predicate"].astype(str).str.strip().str.lower().eq("relation")
            & df["object"].astype(str).str.strip().str.lower().eq("value")
        )
    ].copy()

    # 去掉明显空行
    df = df[
        (df["subject"].astype(str).str.strip() != "")
        & (df["predicate"].astype(str).str.strip() != "")
        & (df["object"].astype(str).str.strip() != "")
    ].copy()

    df = df.reset_index(drop=True)

    print(f"[INFO] Loaded rows: {len(df)}")
    return df


def inspect_ontology(df: pd.DataFrame) -> None:
    print("\n=== Head ===")
    print(df.head(20).to_string(index=False))

    print("\n=== Column samples ===")
    print("subject sample:")
    print(df["subject"].dropna().astype(str).head(10).tolist())

    print("\npredicate sample:")
    print(df["predicate"].dropna().astype(str).head(30).tolist())

    print("\nobject sample:")
    print(df["object"].dropna().astype(str).head(10).tolist())

    print("\n=== Predicate value counts (top 50) ===")
    print(
        df["predicate"]
        .dropna()
        .astype(str)
        .map(norm_predicate)
        .value_counts()
        .head(50)
        .to_string()
    )


# =========================
# Extract positives
# =========================
def fetch_subclass_generalizations(df: pd.DataFrame) -> pd.DataFrame:
    """
    NELL ontology 中：
    generalizations 用于 subclass / subproperty
    """
    tmp = df[df["predicate"].map(norm_predicate).eq("generalizations")].copy()

    tmp["axiom_type"] = "subClassOf"
    tmp["subject"] = tmp["subject"].map(safe_str)
    tmp["predicate"] = "rdfs:subClassOf"
    tmp["object"] = tmp["object"].map(safe_str)
    tmp["label"] = 1
    tmp["source"] = "NELL"
    tmp["negative_strategy"] = ""

    tmp = tmp[["axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"]]
    tmp = tmp[(tmp["subject"] != "") & (tmp["object"] != "") & (tmp["subject"] != tmp["object"])]
    tmp = tmp.drop_duplicates()

    return tmp.reset_index(drop=True)


def fetch_domain(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df[df["predicate"].map(norm_predicate).eq("domain")].copy()

    tmp["axiom_type"] = "domain"
    tmp["subject"] = tmp["subject"].map(safe_str)
    tmp["predicate"] = "rdfs:domain"
    tmp["object"] = tmp["object"].map(safe_str)
    tmp["label"] = 1
    tmp["source"] = "NELL"
    tmp["negative_strategy"] = ""

    tmp = tmp[["axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"]]
    tmp = tmp[(tmp["subject"] != "") & (tmp["object"] != "") & (tmp["subject"] != tmp["object"])]
    tmp = tmp.drop_duplicates()

    return tmp.reset_index(drop=True)


def fetch_range(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df[df["predicate"].map(norm_predicate).eq("range")].copy()

    tmp["axiom_type"] = "range"
    tmp["subject"] = tmp["subject"].map(safe_str)
    tmp["predicate"] = "rdfs:range"
    tmp["object"] = tmp["object"].map(safe_str)
    tmp["label"] = 1
    tmp["source"] = "NELL"
    tmp["negative_strategy"] = ""

    tmp = tmp[["axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"]]
    tmp = tmp[(tmp["subject"] != "") & (tmp["object"] != "") & (tmp["subject"] != tmp["object"])]
    tmp = tmp.drop_duplicates()

    return tmp.reset_index(drop=True)


def fetch_subproperty(df_generalizations: pd.DataFrame, domain_df: pd.DataFrame, range_df: pd.DataFrame) -> pd.DataFrame:
    """
    用 domain/range 中出现过的 subject 识别 relation 名称，
    再从 generalizations 中提取 relation hierarchy => subPropertyOf
    """
    relation_names = set(domain_df["subject"].tolist()) | set(range_df["subject"].tolist())

    tmp = df_generalizations.copy()
    tmp = tmp[tmp["subject"].isin(relation_names) & tmp["object"].isin(relation_names)].copy()

    tmp["axiom_type"] = "subPropertyOf"
    tmp["predicate"] = "rdfs:subPropertyOf"

    tmp = tmp[["axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"]]
    tmp = tmp.drop_duplicates()

    return tmp.reset_index(drop=True)


def refine_subclass(df_generalizations: pd.DataFrame, relation_names: set[str]) -> pd.DataFrame:
    """
    subclass = generalizations 中排除 relation hierarchy 后剩下的部分
    """
    tmp = df_generalizations.copy()
    tmp = tmp[~tmp["subject"].isin(relation_names) & ~tmp["object"].isin(relation_names)].copy()

    tmp["axiom_type"] = "subClassOf"
    tmp["predicate"] = "rdfs:subClassOf"

    tmp = tmp[["axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"]]
    tmp = tmp.drop_duplicates()

    return tmp.reset_index(drop=True)


# =========================
# Negative generation
# =========================
def build_inverse_negatives(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    neg = df.copy()
    neg["subject"], neg["object"] = df["object"], df["subject"]
    neg["label"] = 0
    neg["negative_strategy"] = "direction_inversion"
    return neg.reset_index(drop=True)


def build_replacement_negatives(df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
    """
    domain / range 通过替换 object 构造负例
    """
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    candidate_objects = list(df["object"].dropna().unique())
    existing_pairs = set(zip(df["subject"], df["object"]))

    neg_rows = []
    for _, row in df.iterrows():
        subject = row["subject"]
        true_object = row["object"]

        sampled = None
        tries = 0
        while tries < 100:
            obj = random.choice(candidate_objects)
            if obj != true_object and (subject, obj) not in existing_pairs:
                sampled = obj
                break
            tries += 1

        if sampled is None:
            continue

        neg_rows.append({
            "axiom_type": row["axiom_type"],
            "subject": subject,
            "predicate": row["predicate"],
            "object": sampled,
            "label": 0,
            "source": row["source"],
            "negative_strategy": strategy_name
        })

    return pd.DataFrame(neg_rows)


# =========================
# Rendering
# =========================
def add_render_text(df: pd.DataFrame) -> pd.DataFrame:
    def render(row):
        s = short_name(row["subject"])
        o = short_name(row["object"])
        t = row["axiom_type"]

        if t == "subClassOf":
            return f"{s} ⊑ {o}"
        if t == "subPropertyOf":
            return f"{s} ⊑p {o}"
        if t == "domain":
            return f"domain({s}) = {o}"
        if t == "range":
            return f"range({s}) = {o}"
        return f"{s} {row['predicate']} {o}"

    df = df.copy()
    df["axiom_text"] = df.apply(render, axis=1)
    return df


# =========================
# Statistics
# =========================
def build_stats(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    stats_long = (
        dataset.groupby(["axiom_type", "label"])
        .size()
        .reset_index(name="count")
        .sort_values(["axiom_type", "label"])
        .reset_index(drop=True)
    )

    pivot = (
        dataset.groupby(["axiom_type", "label"])
        .size()
        .unstack(fill_value=0)
        .rename(columns={0: "negative_count", 1: "positive_count"})
        .reset_index()
    )

    if "positive_count" not in pivot.columns:
        pivot["positive_count"] = 0
    if "negative_count" not in pivot.columns:
        pivot["negative_count"] = 0

    pivot["total"] = pivot["positive_count"] + pivot["negative_count"]

    total_row = pd.DataFrame([{
        "axiom_type": "TOTAL",
        "positive_count": int(pivot["positive_count"].sum()),
        "negative_count": int(pivot["negative_count"].sum()),
        "total": int(pivot["total"].sum())
    }])

    stats_wide = pd.concat([pivot, total_row], ignore_index=True)
    return stats_long, stats_wide


# =========================
# Main
# =========================
def main():
    print("Loading NELL ontology...")
    df = load_nell_ontology()

    inspect_ontology(df)

    print("\nExtracting positives...")
    domain_pos_all = fetch_domain(df)
    range_pos_all = fetch_range(df)

    relation_names = set(domain_pos_all["subject"].tolist()) | set(range_pos_all["subject"].tolist())

    generalizations_all = fetch_subclass_generalizations(df)
    subprop_pos_all = fetch_subproperty(generalizations_all, domain_pos_all, range_pos_all)
    subclass_pos_all = refine_subclass(generalizations_all, relation_names)

    print("\n[INFO] Raw positive counts:")
    print({
        "subClassOf": len(subclass_pos_all),
        "subPropertyOf": len(subprop_pos_all),
        "domain": len(domain_pos_all),
        "range": len(range_pos_all),
    })

    subclass_pos = cap_positive_df(subclass_pos_all, POSITIVE_CAP_PER_TYPE)
    subprop_pos = cap_positive_df(subprop_pos_all, POSITIVE_CAP_PER_TYPE)
    domain_pos = cap_positive_df(domain_pos_all, POSITIVE_CAP_PER_TYPE)
    range_pos = cap_positive_df(range_pos_all, POSITIVE_CAP_PER_TYPE)

    print(f"[INFO] Positive cap per type = {POSITIVE_CAP_PER_TYPE}")
    print(f"[INFO] balanced subclass positives: {len(subclass_pos)}")
    print(f"[INFO] balanced subProperty positives: {len(subprop_pos)}")
    print(f"[INFO] balanced domain positives: {len(domain_pos)}")
    print(f"[INFO] balanced range positives: {len(range_pos)}")

    print("Building negatives...")
    subclass_neg = build_inverse_negatives(subclass_pos)
    subprop_neg = build_inverse_negatives(subprop_pos)
    domain_neg = build_replacement_negatives(domain_pos, "constraint_replacement")
    range_neg = build_replacement_negatives(range_pos, "constraint_replacement")

    negatives = pd.concat(
        [subclass_neg, subprop_neg, domain_neg, range_neg],
        ignore_index=True
    )

    positives = pd.concat(
        [subclass_pos, subprop_pos, domain_pos, range_pos],
        ignore_index=True
    )

    dataset = pd.concat([positives, negatives], ignore_index=True)

    dataset = dataset.drop_duplicates(
        subset=["axiom_type", "subject", "predicate", "object", "label"]
    ).reset_index(drop=True)

    dataset = add_render_text(dataset)

    out_csv = RAW_DIR / "nell_rdfs_eval_dataset.csv"
    dataset.to_csv(out_csv, index=False, encoding="utf-8-sig")

    stats_long, stats_wide = build_stats(dataset)

    stats_long_csv = PROCESSED_DIR / "nell_rdfs_eval_dataset_stats_long.csv"
    stats_wide_csv = PROCESSED_DIR / "nell_rdfs_eval_dataset_stats_wide.csv"

    stats_long.to_csv(stats_long_csv, index=False, encoding="utf-8-sig")
    stats_wide.to_csv(stats_wide_csv, index=False, encoding="utf-8-sig")

    print("\nDataset saved to:")
    print(out_csv)
    print(stats_long_csv)
    print(stats_wide_csv)

    print("\n=== Long Stats ===")
    print(stats_long)

    print("\n=== Wide Stats ===")
    print(stats_wide)

    print("\nDone.")


if __name__ == "__main__":
    main()