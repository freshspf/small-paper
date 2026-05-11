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
from app.models.explanation_annotation import AnnotationRecord


def reset_demo_tables() -> None:
    with SessionLocal() as db:
        db.query(AnnotationRecord).delete()
        db.query(EvaluationResult).delete()
        db.query(EvaluationTask).delete()
        db.query(DatasetRecord).delete()
        db.query(Dataset).delete()
        db.commit()


def build_csv_bytes() -> bytes:
    lines = [
        "id,axiom_type,axiom_text,subject,predicate,object,label,source,context_info",
        "sample_1,subClassOf,Album ⊑ MusicalWork,Album,subClassOf,MusicalWork,1,demo,ctx1",
        "sample_2,domain,birthPlace domain Person,birthPlace,domain,Person,1,demo,ctx2",
    ]
    return "\n".join(lines).encode("utf-8")


def fake_call_openai_compatible_model(
    base_url: str,
    api_key: str,
    model_name: str,
    prompt: str,
) -> tuple[str, int, float]:
    return ("Judgment Result: Correct\nExplanation: 这是用于标注测试的模拟解释。", 123, 456.0)


def main() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_prompt_templates(db)
        seed_llm_models(db)
    reset_demo_tables()

    client = TestClient(app)

    dataset_resp = client.post(
        "/api/v1/datasets/upload",
        data={"name": "标注测试数据集", "description": "annotation test", "source": "demo"},
        files={"file": ("annotation.csv", io.BytesIO(build_csv_bytes()), "text/csv")},
    )
    dataset_id = dataset_resp.json()["id"]
    model_id = client.get("/api/v1/models").json()[0]["id"]
    prompt_template_id = next(
        item["id"] for item in client.get("/api/v1/prompt-templates").json() if item["is_default"]
    )

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

    task_id = eval_resp.json()["task"]["id"]
    result_id = eval_resp.json()["preview_results"][0]["id"]

    list_resp = client.get(f"/api/v1/annotations/tasks/{task_id}/results")
    print("ANNOTATION LIST STATUS:", list_resp.status_code)
    print("ANNOTATION LIST BODY:", list_resp.json())

    upsert_resp = client.put(
        f"/api/v1/annotations/results/{result_id}",
        json={
            "explanation_label": "correct",
            "annotation_reason": "解释与判断结果一致",
        },
    )
    print("ANNOTATION UPSERT STATUS:", upsert_resp.status_code)
    print("ANNOTATION UPSERT BODY:", upsert_resp.json())

    get_resp = client.get(f"/api/v1/annotations/results/{result_id}")
    print("ANNOTATION GET STATUS:", get_resp.status_code)
    print("ANNOTATION GET BODY:", get_resp.json())

    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 2
    assert upsert_resp.status_code == 200
    assert get_resp.status_code == 200
    assert get_resp.json()["explanation_label"] == "correct"

    print("Annotations API test completed successfully.")


if __name__ == "__main__":
    main()
