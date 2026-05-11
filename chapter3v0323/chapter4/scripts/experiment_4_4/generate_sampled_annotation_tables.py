from __future__ import annotations

import csv
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_4_manual_full"
OUTPUT_DIR = BASE_DIR / "data" / "annotations" / "experiment_4_4_manual_sampled_100"
SAMPLE_SIZE = 100
SEED = 20260505

TARGET_RELATIONS = {
    "rdfs:subClassOf": "subClassOf",
    "owl:subObjectPropertyOf": "subPropertyOf",
    "rdfs:domain": "domain",
    "rdfs:range": "range",
}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def balanced_sample(rows: list[dict[str, str]], seed: int) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {key: [] for key in TARGET_RELATIONS.values()}
    for row in rows:
        mapped = TARGET_RELATIONS.get(row["relation"].strip())
        if mapped:
            grouped[mapped].append(row)

    rng = random.Random(seed)
    for key in grouped:
        rng.shuffle(grouped[key])

    selected: dict[str, list[dict[str, str]]] = {key: [] for key in grouped}
    remaining_slots = min(SAMPLE_SIZE, sum(len(v) for v in grouped.values()))
    base_quota = SAMPLE_SIZE // 4

    # 少数类型全放进去
    for key, items in grouped.items():
        if 0 < len(items) <= base_quota:
            selected[key].extend(items)
            remaining_slots -= len(items)
            grouped[key] = []

    # 剩余位置按轮转方式尽量均衡补齐
    cycle = ["subClassOf", "subPropertyOf", "domain", "range"]
    while remaining_slots > 0:
        moved = False
        ordered = sorted(
            cycle,
            key=lambda k: (len(selected[k]), -len(grouped[k]), cycle.index(k)),
        )
        for key in ordered:
            if remaining_slots <= 0:
                break
            if grouped[key]:
                selected[key].append(grouped[key].pop())
                remaining_slots -= 1
                moved = True
        if not moved:
            break

    final_rows: list[dict[str, str]] = []
    for key in cycle:
        final_rows.extend(selected[key])

    def sort_key(row: dict[str, str]) -> tuple[str, str, str, int]:
        try:
            axiom_no = int(row["公理序号"])
        except Exception:
            axiom_no = 0
        return (row["领域"], row["文档ID"], row["配置轮次"], axiom_no)

    final_rows.sort(key=sort_key)
    return final_rows[:SAMPLE_SIZE]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, input_path in enumerate(sorted(INPUT_DIR.glob("*.csv"))):
        rows = load_rows(input_path)
        if not rows:
            continue
        sampled_rows = balanced_sample(rows, SEED + index)
        save_rows(OUTPUT_DIR / input_path.name, sampled_rows, list(rows[0].keys()))

        relation_counts: dict[str, int] = {"subClassOf": 0, "subPropertyOf": 0, "domain": 0, "range": 0}
        for row in sampled_rows:
            mapped = TARGET_RELATIONS.get(row["relation"].strip())
            if mapped:
                relation_counts[mapped] += 1
        print(input_path.name, len(sampled_rows), relation_counts)


if __name__ == "__main__":
    main()
