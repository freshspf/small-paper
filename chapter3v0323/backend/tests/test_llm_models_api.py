import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import delete

import app.db.base  # noqa: F401
from app.db.base_class import Base
from app.db.create_tables import ensure_sqlite_schema
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.llm_model import LLMModel


TEST_MODEL_NAME = "TEST-GPT-5.4"


def reset_test_state() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    with SessionLocal() as db:
        db.execute(delete(LLMModel).where(LLMModel.name == TEST_MODEL_NAME))
        db.commit()


def main() -> None:
    reset_test_state()
    client = TestClient(app)

    create_payload = {
        "name": TEST_MODEL_NAME,
        "provider": "OpenAI",
        "base_url": "https://api.example.com/v1",
        "api_key": "sk-test-123",
        "model_name": "gpt-5.4",
        "is_default": True,
    }

    create_resp = client.post("/api/v1/models", json=create_payload)
    print("CREATE STATUS:", create_resp.status_code)
    print("CREATE BODY:", create_resp.json())
    assert create_resp.status_code == 201
    model_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/models")
    print("LIST STATUS:", list_resp.status_code)
    print("LIST SIZE:", len(list_resp.json()))
    assert list_resp.status_code == 200
    assert any(item["id"] == model_id for item in list_resp.json())

    get_resp = client.get(f"/api/v1/models/{model_id}")
    print("GET STATUS:", get_resp.status_code)
    print("GET BODY:", get_resp.json())
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == TEST_MODEL_NAME

    update_payload = {
        "provider": "OpenAI-Compatible",
        "model_name": "gpt-5.4-updated",
        "is_default": False,
    }
    update_resp = client.put(f"/api/v1/models/{model_id}", json=update_payload)
    print("UPDATE STATUS:", update_resp.status_code)
    print("UPDATE BODY:", update_resp.json())
    assert update_resp.status_code == 200
    assert update_resp.json()["provider"] == "OpenAI-Compatible"
    assert update_resp.json()["model_name"] == "gpt-5.4-updated"

    delete_resp = client.delete(f"/api/v1/models/{model_id}")
    print("DELETE STATUS:", delete_resp.status_code)
    assert delete_resp.status_code == 204

    final_get_resp = client.get(f"/api/v1/models/{model_id}")
    print("FINAL GET STATUS:", final_get_resp.status_code)
    print("FINAL GET BODY:", final_get_resp.json())
    assert final_get_resp.status_code == 404

    print("LLM model API test completed successfully.")


if __name__ == "__main__":
    main()
