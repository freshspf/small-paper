import io
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.create_tables import create_tables
from app.db.init_db import seed_prompt_templates
from app.db.session import SessionLocal
from app.main import app
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.llm_model import LLMModel


def reset_demo_tables() -> None:
    with SessionLocal() as db:
        db.query(EvaluationResult).delete()
        db.query(EvaluationTask).delete()
        db.query(DatasetRecord).delete()
        db.query(Dataset).delete()
        db.query(LLMModel).delete()
        db.commit()


def build_csv_bytes() -> bytes:
    lines = [
        "id,axiom_type,axiom_text,subject,predicate,object,label,source,context_info",
    ]
    for index in range(1, 11):
        lines.append(
            f"sample_{index},domain,Axiom {index},Subject{index},predicate_{index},Object{index},1,demo_source,Context {index}"
        )
    return "\n".join(lines).encode("utf-8")


def main() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_prompt_templates(db)
    reset_demo_tables()

    client = TestClient(app)

    model_resp = client.post(
        "/api/v1/models",
        json={
            "name": "演示模型",
            "provider": "Mock Provider",
            "base_url": "https://mock.example.com/v1",
            "api_key": "mock-key",
            "model_name": "mock-model",
            "is_default": True,
        },
    )
    model_id = model_resp.json()["id"]

    dataset_resp = client.post(
        "/api/v1/datasets/upload",
        data={
            "name": "模拟评测数据集",
            "description": "用于评测接口联调",
            "source": "demo",
        },
        files={
            "file": ("mock_eval.csv", io.BytesIO(build_csv_bytes()), "text/csv"),
        },
    )
    dataset_id = dataset_resp.json()["id"]

    template_list_resp = client.get("/api/v1/prompt-templates")
    prompt_template_id = next(item["id"] for item in template_list_resp.json() if item["is_default"])

    eval_resp = client.post(
        "/api/v1/evaluations/mock",
        json={
            "dataset_id": dataset_id,
            "model_id": model_id,
            "prompt_template_id": prompt_template_id,
        },
    )
    print("MOCK EVAL STATUS:", eval_resp.status_code)
    print("MOCK EVAL BODY:", eval_resp.json())

    task_id = eval_resp.json()["task"]["id"]

    task_resp = client.get(f"/api/v1/evaluations/{task_id}")
    print("TASK STATUS:", task_resp.status_code)
    print("TASK BODY:", task_resp.json())

    results_resp = client.get(f"/api/v1/evaluations/{task_id}/results")
    print("RESULTS STATUS:", results_resp.status_code)
    print("RESULTS SIZE:", len(results_resp.json()))
    print("RESULTS FIRST ROW:", results_resp.json()[0])

    assert model_resp.status_code == 201
    assert dataset_resp.status_code == 201
    assert eval_resp.status_code == 201
    assert eval_resp.json()["task"]["status"] == "succeeded"
    assert eval_resp.json()["result_count"] == 10
    assert task_resp.status_code == 200
    assert results_resp.status_code == 200
    assert len(results_resp.json()) == 10

    print("Mock evaluation API test completed successfully.")


if __name__ == "__main__":
    main()
