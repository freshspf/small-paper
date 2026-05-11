import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON


# =========================
# Config
# =========================
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"
REQUEST_SLEEP_SECONDS = 0.2
MAX_RETRIES = 3
SPARQL_TIMEOUT = 60

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "dbpedia" / "raw" / "rdfs_eval_dataset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "dbpedia" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "uri_context_mapping.csv"


# =========================
# Utils
# =========================
def short_uri(uri: str) -> str:
    """从 URI 中提取最后一段短名称。"""
    if not uri or not isinstance(uri, str):
        return ""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def normalize_text(text: Optional[str], max_len: int = 240) -> str:
    """清洗文本并截断长度。"""
    if not text:
        return ""

    text = str(text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text


def detect_kind(uri: str) -> str:
    """
    基于 URI 粗略判断类型。
    DBpedia ontology 中多数类和属性都在同一命名空间下，
    因此这里只做保守初始化，最终以 SPARQL 查询结果为准。
    """
    if not uri:
        return "Unknown"
    return "Unknown"


def extract_unique_uris(df: pd.DataFrame) -> list[str]:
    """从数据集中提取 subject 和 object 的唯一 URI。"""
    uris = set()

    for col in ["subject", "object"]:
        if col in df.columns:
            values = df[col].dropna().astype(str).tolist()
            uris.update(v for v in values if v.startswith("http"))

    return sorted(uris)


# =========================
# SPARQL
# =========================
def run_sparql_query(query: str, max_retries: int = MAX_RETRIES, timeout: int = SPARQL_TIMEOUT):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(timeout)
            results = sparql.query().convert()
            return results["results"]["bindings"]
        except Exception as e:
            last_error = e
            print(f"[WARN] SPARQL query failed (attempt {attempt}/{max_retries}): {e}")
            time.sleep(attempt * 2)
    raise last_error


def get_binding_value(binding: dict, key: str) -> str:
    if key not in binding:
        return ""
    return binding[key].get("value", "")


def query_uri_info(uri: str) -> dict:
    """
    查询单个 URI 的上下文信息。
    优先获取：
    - 英文 label
    - 英文 abstract
    - 英文 comment
    - rdf:type
    """
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbo:  <http://dbpedia.org/ontology/>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?label ?abstract ?comment ?type
    WHERE {{
      OPTIONAL {{
        <{uri}> rdfs:label ?label .
        FILTER (lang(?label) = 'en')
      }}
      OPTIONAL {{
        <{uri}> dbo:abstract ?abstract .
        FILTER (lang(?abstract) = 'en')
      }}
      OPTIONAL {{
        <{uri}> rdfs:comment ?comment .
        FILTER (lang(?comment) = 'en')
      }}
      OPTIONAL {{
        <{uri}> rdf:type ?type .
        FILTER (
          ?type = rdf:Property ||
          ?type = owl:ObjectProperty ||
          ?type = owl:DatatypeProperty ||
          ?type = owl:Class ||
          ?type = rdfs:Class
        )
      }}
    }}
    LIMIT 20
    """

    # 注意：这里 query 中用了 owl: 前缀，需要补上
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbo:  <http://dbpedia.org/ontology/>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?label ?abstract ?comment ?type
    WHERE {
      OPTIONAL {
        <%s> rdfs:label ?label .
        FILTER (lang(?label) = 'en')
      }
      OPTIONAL {
        <%s> dbo:abstract ?abstract .
        FILTER (lang(?abstract) = 'en')
      }
      OPTIONAL {
        <%s> rdfs:comment ?comment .
        FILTER (lang(?comment) = 'en')
      }
      OPTIONAL {
        <%s> rdf:type ?type .
        FILTER (
          ?type = rdf:Property ||
          ?type = owl:ObjectProperty ||
          ?type = owl:DatatypeProperty ||
          ?type = owl:Class ||
          ?type = rdfs:Class
        )
      }
    }
    LIMIT 20
    """ % (uri, uri, uri, uri)

    rows = run_sparql_query(query)

    label_en = ""
    abstract_en = ""
    comment_en = ""
    raw_types = set()

    for row in rows:
        if not label_en:
            label_en = get_binding_value(row, "label")
        if not abstract_en:
            abstract_en = get_binding_value(row, "abstract")
        if not comment_en:
            comment_en = get_binding_value(row, "comment")

        t = get_binding_value(row, "type")
        if t:
            raw_types.add(t)

    kind = classify_kind_from_types(raw_types)

    status = "ok"
    if not abstract_en and not comment_en:
        if label_en:
            status = "partial"
        else:
            status = "missing"

    return {
        "uri": uri,
        "name": short_uri(uri),
        "kind": kind,
        "label_en": normalize_text(label_en, max_len=120),
        "abstract_en": normalize_text(abstract_en, max_len=240),
        "comment_en": normalize_text(comment_en, max_len=240),
        "source": "DBpedia_SPARQL",
        "status": status,
    }


def classify_kind_from_types(type_uris: set[str]) -> str:
    """根据 rdf:type 结果判断 Class / Property / Unknown。"""
    if not type_uris:
        return "Unknown"

    property_types = {
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
        "http://www.w3.org/2002/07/owl#ObjectProperty",
        "http://www.w3.org/2002/07/owl#DatatypeProperty",
    }
    class_types = {
        "http://www.w3.org/2002/07/owl#Class",
        "http://www.w3.org/2000/01/rdf-schema#Class",
    }

    if any(t in property_types for t in type_uris):
        return "Property"
    if any(t in class_types for t in type_uris):
        return "Class"
    return "Unknown"


# =========================
# Main
# =========================
def main():
    print("=== Build URI Context Mapping ===")
    print(f"INPUT_CSV : {INPUT_CSV}")
    print(f"OUTPUT_CSV: {OUTPUT_CSV}")

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"未找到输入文件：{INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    required_columns = {"subject", "object"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"数据集缺少必要字段: {missing_columns}")

    uri_list = extract_unique_uris(df)
    print(f"[INFO] 提取到唯一 URI 数量: {len(uri_list)}")

    rows = []
    for idx, uri in enumerate(uri_list, start=1):
        print(f"[{idx}/{len(uri_list)}] Querying: {uri}")
        try:
            info = query_uri_info(uri)
        except Exception as e:
            print(f"[ERROR] Failed to query {uri}: {e}")
            info = {
                "uri": uri,
                "name": short_uri(uri),
                "kind": detect_kind(uri),
                "label_en": "",
                "abstract_en": "",
                "comment_en": "",
                "source": "DBpedia_SPARQL",
                "status": "missing",
            }

        rows.append(info)
        time.sleep(REQUEST_SLEEP_SECONDS)

    mapping_df = pd.DataFrame(rows)

    # 去重保险
    mapping_df = mapping_df.drop_duplicates(subset=["uri"]).reset_index(drop=True)

    # 保存
    mapping_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n=== Summary ===")
    print(mapping_df["status"].value_counts(dropna=False).to_string())
    print("\n=== Kind Distribution ===")
    print(mapping_df["kind"].value_counts(dropna=False).to_string())

    print(f"\n[INFO] 映射文件已保存：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()
