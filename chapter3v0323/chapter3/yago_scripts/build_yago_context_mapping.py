import re
import time
import random
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup


RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SCHEMA_PROPERTIES_CSV = "https://schema.org/version/latest/schemaorg-current-http-properties.csv"
WIKIPEDIA_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "yago" / "raw" / "yago_rdfs_eval_dataset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "yago" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "yago_uri_context_mapping.csv"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; YAGOContextBuilder/1.0; +https://example.org)"
}

REQUEST_SLEEP_SECONDS = 0.3
MAX_DESC_LEN = 240


# =========================
# Utils
# =========================
def safe_str(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_text(text: Optional[str], max_len: int = MAX_DESC_LEN) -> str:
    text = safe_str(text)
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text


def short_uri(uri: str) -> str:
    if not uri or not isinstance(uri, str):
        return ""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def is_property_uri(uri: str) -> bool:
    uri = safe_str(uri)
    return "schema.org" in uri


def infer_kind(uri: str) -> str:
    return "Property" if is_property_uri(uri) else "Class"


def extract_unique_uris(df: pd.DataFrame) -> list[str]:
    uris = set()
    for col in ["subject", "object"]:
        if col in df.columns:
            vals = df[col].dropna().astype(str).tolist()
            uris.update(v for v in vals if v.startswith("http"))
    return sorted(uris)


def normalize_schema_uri(value: str) -> str:
    value = safe_str(value)
    if not value:
        return ""
    if value.startswith("https://schema.org/"):
        return value.replace("https://schema.org/", "http://schema.org/")
    if value.startswith("http://schema.org/"):
        return value
    if value.startswith("schema:"):
        return "http://schema.org/" + value.split("schema:")[-1]
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return "http://schema.org/" + value


def make_fallback_description(name: str, kind: str) -> str:
    if kind == "Property":
        return f"{name} is a property in the knowledge base."
    return f"{name} is a class in the knowledge base."


# =========================
# Schema.org loading
# =========================
def load_schema_properties_df() -> pd.DataFrame:
    df = pd.read_csv(SCHEMA_PROPERTIES_CSV)
    df = df.fillna("")
    return df


def build_schema_mapping(schema_df: pd.DataFrame) -> dict[str, dict]:
    """
    只给 schema.org 属性建映射。
    """
    mapping = {}
    id_col = "id" if "id" in schema_df.columns else schema_df.columns[0]

    # 可能存在的描述列
    desc_col = None
    for c in schema_df.columns:
        if c.lower() in {"comment", "description", "rdfs:comment"}:
            desc_col = c
            break

    label_col = None
    for c in schema_df.columns:
        if c.lower() in {"label", "rdfs:label"}:
            label_col = c
            break

    domain_col = None
    for c in schema_df.columns:
        if c.lower() == "domainincludes":
            domain_col = c
            break

    range_col = None
    for c in schema_df.columns:
        if c.lower() == "rangeincludes":
            range_col = c
            break

    for _, row in schema_df.iterrows():
        uri = normalize_schema_uri(row[id_col])
        if not uri:
            continue

        name = short_uri(uri)
        label_en = normalize_text(row[label_col]) if label_col else name
        desc = normalize_text(row[desc_col]) if desc_col else ""

        extra_parts = []
        if domain_col and safe_str(row[domain_col]):
            extra_parts.append(f"domainIncludes: {safe_str(row[domain_col])}")
        if range_col and safe_str(row[range_col]):
            extra_parts.append(f"rangeIncludes: {safe_str(row[range_col])}")

        extra_info = " | ".join(extra_parts)

        mapping[uri] = {
            "uri": uri,
            "name": name,
            "kind": "Property",
            "label_en": label_en or name,
            "description": desc,
            "extra_info": normalize_text(extra_info, max_len=180),
            "source": "schema.org",
            "status": "ok" if desc else "partial",
        }

    return mapping


# =========================
# Wikipedia fallback
# =========================
def wikipedia_title_candidates(name: str) -> list[str]:
    """
    给一个短名称生成可能的 Wikipedia 页面标题。
    """
    name = safe_str(name)
    if not name:
        return []

    candidates = []
    base = name.replace("_", " ").strip()

    # 原始
    candidates.append(base)

    # 首字母大写
    candidates.append(base[:1].upper() + base[1:] if base else base)

    # 驼峰拆词
    spaced = re.sub(r"(?<!^)([A-Z])", r" \1", name).replace("_", " ").strip()
    if spaced and spaced not in candidates:
        candidates.append(spaced)

    # 去重保序
    seen = set()
    result = []
    for c in candidates:
        cc = c.strip()
        if cc and cc not in seen:
            result.append(cc)
            seen.add(cc)
    return result


def fetch_wikipedia_summary(name: str) -> tuple[str, str]:
    """
    返回: (description, source)
    """
    for title in wikipedia_title_candidates(name):
        url = WIKIPEDIA_SUMMARY_API.format(title=quote(title))
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            extract = normalize_text(data.get("extract", ""))
            if extract:
                return extract, f"Wikipedia:{title}"
        except Exception:
            continue
        finally:
            time.sleep(REQUEST_SLEEP_SECONDS)
    return "", ""


# =========================
# Baidu Baike fallback
# =========================
def fetch_baidu_baike_summary(name: str) -> tuple[str, str]:
    """
    很轻量的兜底抓取。
    只尝试抓页面标题和 meta description，避免抓整页正文。
    """
    if not name:
        return "", ""

    urls = [
        f"https://baike.baidu.com/item/{quote(name)}",
        f"https://baike.baidu.com/item/{quote(name.replace('_', ' '))}",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 优先 meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                desc = normalize_text(meta_desc.get("content"))
                if desc:
                    return desc, f"BaiduBaike:{name}"

            # 再尝试页面首段
            summary_div = soup.find("div", class_=re.compile("lemma-summary"))
            if summary_div:
                desc = normalize_text(summary_div.get_text(" ", strip=True))
                if desc:
                    return desc, f"BaiduBaike:{name}"

        except Exception:
            continue
        finally:
            time.sleep(REQUEST_SLEEP_SECONDS)

    return "", ""


# =========================
# Main logic
# =========================
def build_context_row(uri: str, schema_mapping: dict[str, dict]) -> dict:
    uri = safe_str(uri)
    name = short_uri(uri)
    kind = infer_kind(uri)

    # 1) schema.org 结构化优先
    if uri in schema_mapping:
        row = schema_mapping[uri].copy()
        if not row["description"]:
            row["description"] = make_fallback_description(row["name"], row["kind"])
            row["status"] = "partial"
        return row

    # 2) Wikipedia 回退
    wiki_desc, wiki_source = fetch_wikipedia_summary(name)
    if wiki_desc:
        return {
            "uri": uri,
            "name": name,
            "kind": kind,
            "label_en": name,
            "description": wiki_desc,
            "extra_info": "",
            "source": wiki_source,
            "status": "ok",
        }

    # 3) 百度百科回退
    baidu_desc, baidu_source = fetch_baidu_baike_summary(name)
    if baidu_desc:
        return {
            "uri": uri,
            "name": name,
            "kind": kind,
            "label_en": name,
            "description": baidu_desc,
            "extra_info": "",
            "source": baidu_source,
            "status": "ok",
        }

    # 4) 模板兜底
    return {
        "uri": uri,
        "name": name,
        "kind": kind,
        "label_en": name,
        "description": make_fallback_description(name, kind),
        "extra_info": "",
        "source": "fallback",
        "status": "fallback",
    }


def main():
    print("=== Build YAGO Context Mapping ===")
    print(f"INPUT_CSV : {INPUT_CSV}")
    print(f"OUTPUT_CSV: {OUTPUT_CSV}")

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"未找到输入文件：{INPUT_CSV}")

    dataset_df = pd.read_csv(INPUT_CSV)
    required_columns = {"subject", "object"}
    missing = required_columns - set(dataset_df.columns)
    if missing:
        raise ValueError(f"数据集缺少必要字段: {missing}")

    uri_list = extract_unique_uris(dataset_df)
    print(f"[INFO] 唯一 URI 数量: {len(uri_list)}")

    print("[INFO] Loading schema.org property definitions...")
    schema_df = load_schema_properties_df()
    schema_mapping = build_schema_mapping(schema_df)
    print(f"[INFO] schema.org property mapping size: {len(schema_mapping)}")

    rows = []
    for idx, uri in enumerate(uri_list, start=1):
        print(f"[{idx}/{len(uri_list)}] Building context for: {uri}")
        row = build_context_row(uri, schema_mapping)
        rows.append(row)

    mapping_df = pd.DataFrame(rows).drop_duplicates(subset=["uri"]).reset_index(drop=True)
    mapping_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n=== Summary ===")
    print(mapping_df["status"].value_counts(dropna=False).to_string())

    print("\n=== Source Distribution ===")
    print(mapping_df["source"].value_counts(dropna=False).head(20).to_string())

    print(f"\n[INFO] 输出文件已保存：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()