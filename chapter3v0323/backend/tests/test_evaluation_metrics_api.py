import io
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.create_tables import create_tables
from app.db.init_db import seed_prompt_templates
from app.db.init_models import seed_llm_models
from app.db.session import SessionLocal
from app.main import app
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult


def reset_demo_tables() -> None:
    with SessionLocal() as db:
        db.query(EvaluationResult).delete()
        db.query(EvaluationTask).delete()
        db.query(DatasetRecord).delete()
        db.query(Dataset).delete()
        db.commit()


def build_csv_bytes() -> bytes:
    lines = [
        "id,axiom_type,axiom_text,subject,predicate,object,label,source,context_info",
        "sample_1,domain,Axiom 1,s1,p1,o1,1,demo,ctx1",
        "sample_2,domain,Axiom 2,s2,p2,o2,0,demo,ctx2",
        "sample_3,range,Axiom 3,s3,p3,o3,1,demo,ctx3",
        "sample_4,range,Axiom 4,s4,p4,o4,0,demo,ctx4",
    ]
    return "\n".join(lines).encode("utf-8")


RESPONSES = [
    ("Judgment Result: Correct\nExplanation: ok", 100, 500.0),
    ("Judgment Result: Correct\nExplanation: wrong positive", 100, 500.0),
    ("Judgment Result: Incorrect\nExplanation: wrong negative", 100, 500.0),
    ("Judgment Result: Incorrect\nExplanation: ok", 100, 500.0),
]


def main() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_prompt_templates(db)
        seed_llm_models(db)
    reset_demo_tables()

    client = TestClient(app)

    dataset_resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "指标测试数据集", "description": "用于 metrics 接口测试", "source": "demo"},
        files={"file": ("metrics.csv", io.BytesIO(build_csv_bytes()), "text/csv")},
    )
    dataset_id = dataset_resp.json()["id"]

    model_id = client.get("/api/v1/models").json()[0]["id"]
    prompt_template_id = next(
        item["id"] for item in client.get("/api/v1/prompt-templates").json() if item["is_default"]
    )

    with patch("app.services.evaluation_service.call_openai_compatible_model", side_effect=RESPONSES):
        eval_resp = client.post(
            "/api/v1/evaluations",
            json={
                "dataset_id": dataset_id,
                "model_id": model_id,
                "prompt_template_id": prompt_template_id,
            },
        )

    task_id = eval_resp.json()["task"]["id"]
    metrics_resp = client.get(f"/api/v1/evaluations/{task_id}/metrics")
    body = metrics_resp.json()

    print("METRICS STATUS:", metrics_resp.status_code)
    print("METRICS BODY:", body)

    assert metrics_resp.status_code == 200
    assert body["overall"]["total"] == 4
    assert body["overall"]["accuracy"] == 0.5
    assert body["overall"]["precision"] == 0.5
    assert body["overall"]["recall"] == 0.5
    assert body["overall"]["f1"] == 0.5

    assert body["by_axiom_type"]["domain"]["total"] == 2
    assert body["by_axiom_type"]["domain"]["accuracy"] == 0.5
    assert body["by_axiom_type"]["range"]["total"] == 2
    assert body["by_axiom_type"]["range"]["accuracy"] == 0.5

    print("Evaluation metrics API test completed successfully.")


if __name__ == "__main__":
    main()
