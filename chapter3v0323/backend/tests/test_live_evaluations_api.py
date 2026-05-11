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
        "sample_1,subClassOf,Album ⊑ MusicalWork,Album,subClassOf,MusicalWork,1,demo_source,Album 表示一种音乐作品",
        "sample_2,domain,birthPlace domain Person,birthPlace,domain,Person,1,demo_source,birthPlace 的主语通常是人",
    ]
    return "\n".join(lines).encode("utf-8")


def fake_call_openai_compatible_model(
    base_url: str,
    api_key: str,
    model_name: str,
    prompt: str,
) -> tuple[str, int, float]:
    if "Album" in prompt:
        return (
            "Judgment Result: Correct\nExplanation: Album 作为音乐作品的子类关系在语义上是合理的。",
            321,
            812.6,
        )
    return (
        "Judgment Result: Incorrect\nExplanation: 该定义域约束与给定语义存在冲突。",
        287,
        756.2,
    )


def main() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_prompt_templates(db)
        seed_llm_models(db)
    reset_demo_tables()

    client = TestClient(app)

    dataset_resp = client.post(
        "/api/v1/datasets/upload",
        data={
            "name": "真实评测测试数据集",
            "description": "用于真实评测接口测试",
            "source": "demo",
        },
        files={
            "file": ("live_eval.csv", io.BytesIO(build_csv_bytes()), "text/csv"),
        },
    )
    dataset_id = dataset_resp.json()["id"]

    model_list_resp = client.get("/api/v1/models")
    model_id = model_list_resp.json()[0]["id"]

    template_list_resp = client.get("/api/v1/prompt-templates")
    prompt_template_id = next(item["id"] for item in template_list_resp.json() if item["is_default"])

    with patch(
        "app.services.evaluation_service.call_openai_compatible_model",
        side_effect=fake_call_openai_compatible_model,
    ):
        eval_resp = client.post(
            "/api/v1/evaluations",
            json={
                "dataset_id": dataset_id,
                "model_id": model_id,
                "prompt_template_id": prompt_template_id,
            },
        )

    print("LIVE EVAL STATUS:", eval_resp.status_code)
    print("LIVE EVAL BODY:", eval_resp.json())

    body = eval_resp.json()
    assert eval_resp.status_code == 201
    assert body["task"]["status"] == "succeeded"
    assert body["result_count"] == 2
    assert body["preview_results"][0]["judgment_result"] in {"Correct", "Incorrect"}
    assert body["preview_results"][0]["raw_response"] is not None

    print("Live evaluation API test completed successfully.")


if __name__ == "__main__":
    main()
