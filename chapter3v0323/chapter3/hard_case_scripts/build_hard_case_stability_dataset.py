import pandas as pd
import re
from pathlib import Path


BASE_DIR = Path("/Users/ning/Developer/project26/exps/chapter3v0323/chapter3/data/hard_case/processed")
INPUT_CSV = BASE_DIR / "hard_case_stability_eval_dataset_with_context.csv"
OUTPUT_CSV = BASE_DIR / "hard_case_stability_dataset_all_templates.csv"


def parse_subclass_axiom(text: str):
    """
    解析: A ⊑ B
    """
    parts = text.split("⊑")
    if len(parts) != 2:
        raise ValueError(f"无法解析 subClassOf 公理: {text}")
    left = parts[0].strip()
    right = parts[1].strip()
    return left, right


def parse_subproperty_axiom(text: str):
    """
    解析: P ⊑p Q
    """
    parts = text.split("⊑p")
    if len(parts) != 2:
        raise ValueError(f"无法解析 subPropertyOf 公理: {text}")
    left = parts[0].strip()
    right = parts[1].strip()
    return left, right


def parse_domain_axiom(text: str):
    """
    解析: domain(P) = C
    """
    m = re.match(r"domain\((.*?)\)\s*=\s*(.*)", text)
    if not m:
        raise ValueError(f"无法解析 domain 公理: {text}")
    prop = m.group(1).strip()
    cls = m.group(2).strip()
    return prop, cls


def parse_range_axiom(text: str):
    """
    解析: range(P) = C
    """
    m = re.match(r"range\((.*?)\)\s*=\s*(.*)", text)
    if not m:
        raise ValueError(f"无法解析 range 公理: {text}")
    prop = m.group(1).strip()
    cls = m.group(2).strip()
    return prop, cls


def generate_templates(axiom_type: str, axiom_text: str):
    """
    生成模板2-5
    返回 dict: {2: xxx, 3: xxx, 4: xxx, 5: xxx}
    """
    if axiom_type == "subClassOf":
        A, B = parse_subclass_axiom(axiom_text)
        return {
            2: f"{A} is a subclass of {B}.",
            3: f"Every instance of {A} is also an instance of {B}.",
            4: f"If an entity belongs to class {A}, then it also belongs to class {B}.",
            5: f"The class {A} is included in the class {B}."
        }

    elif axiom_type == "subPropertyOf":
        P, Q = parse_subproperty_axiom(axiom_text)
        return {
            2: f"{P} is a subproperty of {Q}.",
            3: f"If two resources are related by {P}, then they are also related by {Q}.",
            4: f"For any x and y, if x {P} y holds, then x {Q} y also holds.",
            5: f"The property {P} is more specific than the property {Q}."
        }

    elif axiom_type == "domain":
        P, C = parse_domain_axiom(axiom_text)
        return {
            2: f"The domain of {P} is {C}.",
            3: f"If a resource uses property {P} as subject, then it should belong to class {C}.",
            4: f"For any x and y, if x {P} y holds, then x is an instance of {C}.",
            5: f"Property {P} can only be applied to subjects of class {C}."
        }

    elif axiom_type == "range":
        P, C = parse_range_axiom(axiom_text)
        return {
            2: f"The range of {P} is {C}.",
            3: f"If a resource appears as the object of property {P}, then it should belong to class {C}.",
            4: f"For any x and y, if x {P} y holds, then y is an instance of {C}.",
            5: f"Property {P} can only point to objects of class {C}."
        }

    else:
        raise ValueError(f"未知的 axiom_type: {axiom_type}")


def build_all_templates(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)

    required_cols = ["id", "axiom_type", "axiom_text", "context_info", "label"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"输入文件缺少必要字段: {col}")

    rows = []

    for _, row in df.iterrows():
        sample_id = row["id"]
        axiom_type = row["axiom_type"]
        axiom_text = row["axiom_text"]
        context_info = row["context_info"]
        label = row["label"]

        # 模板1：原始形式
        rows.append({
            "original_id": sample_id,
            "template_id": 1,
            "variant_id": f"{sample_id}_t1",
            "axiom_type": axiom_type,
            "axiom_text": axiom_text,
            "context_info": context_info,
            "label": label
        })

        # 模板2-5：自动生成
        templates = generate_templates(axiom_type, axiom_text)
        for template_id, template_text in templates.items():
            rows.append({
                "original_id": sample_id,
                "template_id": template_id,
                "variant_id": f"{sample_id}_t{template_id}",
                "axiom_type": axiom_type,
                "axiom_text": template_text,
                "context_info": context_info,
                "label": label
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"生成完成，共 {len(out_df)} 条样本，已保存到: {output_csv}")
    print(out_df.head(10))


if __name__ == "__main__":
    build_all_templates(INPUT_CSV, OUTPUT_CSV)
