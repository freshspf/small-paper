import random
import time
from pathlib import Path

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON


YAGO_ENDPOINT = "https://yago-knowledge.org/sparql/query"
SCHEMA_PROPERTIES_CSV = "https://schema.org/version/latest/schemaorg-current-http-properties.csv"
RANDOM_SEED = 42
TARGET_POSITIVE_PER_TYPE = 60
YAGO_SUBCLASS_FETCH_LIMIT = 1000
random.seed(RANDOM_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "yago" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "yago" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# SPARQL utilities
# =========================
def run_sparql_query(query: str, max_retries: int = 4, timeout: int = 60) -> list[dict]:
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            sparql = SPARQLWrapper(YAGO_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(timeout)
            results = sparql.query().convert()
            return results["results"]["bindings"]
        except Exception as e:
            last_error = e
            print(f"[WARN] SPARQL query failed (attempt {attempt}/{max_retries}): {e}")
            time.sleep(3 * attempt)
    raise last_error


def extract_value(binding: dict, key: str) -> str:
    return binding[key]["value"]


def short_uri(uri: str) -> str:
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


# =========================
# URI helpers
# =========================
def normalize_schema_uri(value: str) -> str:
    """
    把 schema.org 的值统一转成 http://schema.org/xxx 形式，
    方便和 YAGO / schema 数据混用。
    """
    if not value or not isinstance(value, str):
        return ""

    value = value.strip()

    if value.startswith("https://schema.org/"):
        return value.replace("https://schema.org/", "http://schema.org/")
    if value.startswith("http://schema.org/"):
        return value
    if value.startswith("schema:"):
        return "http://schema.org/" + value.split("schema:")[-1]
    if value.startswith("http://") or value.startswith("https://"):
        return value

    return "http://schema.org/" + value


def is_yago_class_uri(uri: str) -> bool:
    if not uri or not isinstance(uri, str):
        return False
    return uri.startswith("https://yago-knowledge.org/resource/") or uri.startswith("http://yago-knowledge.org/resource/")


# =========================
# Fetch positive axioms
# =========================
def fetch_yago_subclass(limit: int = 1200) -> pd.DataFrame:
    """
    subClassOf 从 YAGO 端点抓。
    """
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?sub ?sup
    WHERE {{
      ?sub rdfs:subClassOf ?sup .
      FILTER(isIRI(?sub) && isIRI(?sup))
      FILTER(?sub != ?sup)
    }}
    LIMIT {limit}
    """
    rows = run_sparql_query(query)

    data = []
    for r in rows:
        sub = extract_value(r, "sub")
        sup = extract_value(r, "sup")

        if is_yago_class_uri(sub) and is_yago_class_uri(sup):
            data.append({
                "axiom_type": "subClassOf",
                "subject": sub,
                "predicate": "rdfs:subClassOf",
                "object": sup,
                "label": 1,
                "source": "YAGO",
                "negative_strategy": ""
            })

    return pd.DataFrame(data)


def load_schema_properties_df() -> pd.DataFrame:
    """
    读取 schema.org 官方 properties CSV。
    这个文件包含 supersedes / domainIncludes / rangeIncludes 等字段。
    """
    df = pd.read_csv(SCHEMA_PROPERTIES_CSV)
    df = df.fillna("")
    return df


def split_multi_values(value: str) -> list[str]:
    """
    schema.org CSV 里的 domainIncludes / rangeIncludes / supersedes 等字段
    可能是逗号分隔或空。
    """
    if not value or not isinstance(value, str):
        return []

    # 有些字段是逗号分隔
    parts = [v.strip() for v in value.split(",") if v.strip()]
    return parts


def fetch_schema_subproperty(schema_df: pd.DataFrame) -> pd.DataFrame:
    """
    通过 schema.org properties CSV 构造 subPropertyOf。
    CSV 里一般没有直接名为 subPropertyOf 的列，但 supersedes / inverseOf 等可见。
    这里优先尝试 'subPropertyOf'，如果没有则回退到 'supersedes' 不适合作为子属性；
    因此此处只在列存在时构造，避免伪造。
    """
    candidate_cols = [c for c in schema_df.columns if c.lower() in {"subpropertyof", "rdfs:subpropertyof"}]

    if not candidate_cols:
        print("[WARN] schema.org properties CSV 中未发现 subPropertyOf 列，subPropertyOf 正例将为空。")
        return pd.DataFrame(columns=[
            "axiom_type", "subject", "predicate", "object", "label", "source", "negative_strategy"
        ])

    col = candidate_cols[0]
    rows = []

    id_col = "id" if "id" in schema_df.columns else schema_df.columns[0]

    for _, row in schema_df.iterrows():
        prop = normalize_schema_uri(str(row[id_col]))
        supers = split_multi_values(str(row[col]))

        for sup in supers:
            sup_uri = normalize_schema_uri(sup)
            if prop and sup_uri and prop != sup_uri:
                rows.append({
                    "axiom_type": "subPropertyOf",
                    "subject": prop,
                    "predicate": "rdfs:subPropertyOf",
                    "object": sup_uri,
                    "label": 1,
                    "source": "schema.org",
                    "negative_strategy": ""
                })

    return pd.DataFrame(rows)


def fetch_schema_domain(schema_df: pd.DataFrame) -> pd.DataFrame:
    """
    schema.org 用 domainIncludes 表达属性的 domain。
    """
    domain_col = None
    for c in schema_df.columns:
        if c.lower() == "domainincludes":
            domain_col = c
            break

    if domain_col is None:
        raise ValueError("schema.org properties CSV 中未找到 domainIncludes 列。")

    id_col = "id" if "id" in schema_df.columns else schema_df.columns[0]

    rows = []
    for _, row in schema_df.iterrows():
        prop = normalize_schema_uri(str(row[id_col]))
        domains = split_multi_values(str(row[domain_col]))

        for d in domains:
            d_uri = normalize_schema_uri(d)
            if prop and d_uri and prop != d_uri:
                rows.append({
                    "axiom_type": "domain",
                    "subject": prop,
                    "predicate": "rdfs:domain",
                    "object": d_uri,
                    "label": 1,
                    "source": "schema.org",
                    "negative_strategy": ""
                })

    return pd.DataFrame(rows)


def fetch_schema_range(schema_df: pd.DataFrame) -> pd.DataFrame:
    """
    schema.org 用 rangeIncludes 表达属性的 range。
    """
    range_col = None
    for c in schema_df.columns:
        if c.lower() == "rangeincludes":
            range_col = c
            break

    if range_col is None:
        raise ValueError("schema.org properties CSV 中未找到 rangeIncludes 列。")

    id_col = "id" if "id" in schema_df.columns else schema_df.columns[0]

    rows = []
    for _, row in schema_df.iterrows():
        prop = normalize_schema_uri(str(row[id_col]))
        ranges = split_multi_values(str(row[range_col]))

        for r in ranges:
            r_uri = normalize_schema_uri(r)
            if prop and r_uri and prop != r_uri:
                rows.append({
                    "axiom_type": "range",
                    "subject": prop,
                    "predicate": "rdfs:range",
                    "object": r_uri,
                    "label": 1,
                    "source": "schema.org",
                    "negative_strategy": ""
                })

    return pd.DataFrame(rows)


# =========================
# Cleaning
# =========================
def clean_positive_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["axiom_type", "subject", "predicate", "object"]).copy()
    df = df[df["subject"] != df["object"]].copy()
    return df.reset_index(drop=True)


def balance_positive_sets(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    counts = {k: len(v) for k, v in dfs.items()}
    print("[INFO] Positive counts before balancing:", counts)

    non_empty_counts = [len(v) for v in dfs.values() if len(v) > 0]
    if not non_empty_counts:
        raise ValueError("四类正例都为空，无法构建数据集。")

    print(f"[INFO] Positive cap per type = {TARGET_POSITIVE_PER_TYPE}")

    balanced = {}
    for k, df in dfs.items():
        if len(df) <= TARGET_POSITIVE_PER_TYPE:
            if len(df) < TARGET_POSITIVE_PER_TYPE:
                print(f"[WARN] {k} has only {len(df)} rows, smaller than target cap.")
            balanced[k] = df.copy().reset_index(drop=True)
        else:
            balanced[k] = df.sample(
                n=TARGET_POSITIVE_PER_TYPE, random_state=RANDOM_SEED
            ).reset_index(drop=True)

    return balanced


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
        s = short_uri(row["subject"])
        o = short_uri(row["object"])
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
# Main pipeline
# =========================
def main():
    print("Fetching positives from YAGO + schema.org...")

    subclass_pos = clean_positive_df(fetch_yago_subclass(YAGO_SUBCLASS_FETCH_LIMIT))
    time.sleep(1)

    schema_df = load_schema_properties_df()

    subprop_pos = clean_positive_df(fetch_schema_subproperty(schema_df))
    domain_pos = clean_positive_df(fetch_schema_domain(schema_df))
    range_pos = clean_positive_df(fetch_schema_range(schema_df))

    positive_dict = {
        "subClassOf": subclass_pos,
        "subPropertyOf": subprop_pos,
        "domain": domain_pos,
        "range": range_pos,
    }

    balanced_positive_dict = balance_positive_sets(positive_dict)

    subclass_pos = balanced_positive_dict["subClassOf"]
    subprop_pos = balanced_positive_dict["subPropertyOf"]
    domain_pos = balanced_positive_dict["domain"]
    range_pos = balanced_positive_dict["range"]

    positives = pd.concat(
        [subclass_pos, subprop_pos, domain_pos, range_pos],
        ignore_index=True
    )

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

    dataset = pd.concat([positives, negatives], ignore_index=True)

    dataset = dataset.drop_duplicates(
        subset=["axiom_type", "subject", "predicate", "object", "label"]
    ).reset_index(drop=True)

    dataset = add_render_text(dataset)

    out_csv = RAW_DIR / "yago_rdfs_eval_dataset.csv"
    dataset.to_csv(out_csv, index=False, encoding="utf-8-sig")

    stats_long, stats_wide = build_stats(dataset)

    stats_long_csv = PROCESSED_DIR / "yago_rdfs_eval_dataset_stats_long.csv"
    stats_wide_csv = PROCESSED_DIR / "yago_rdfs_eval_dataset_stats_wide.csv"

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
