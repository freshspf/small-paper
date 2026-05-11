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


def initialize_templates() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_prompt_templates(db)


def main() -> None:
    initialize_templates()
    client = TestClient(app)

    list_resp = client.get("/api/v1/prompt-templates")
    print("LIST STATUS:", list_resp.status_code)
    print("LIST SIZE:", len(list_resp.json()))

    templates = list_resp.json()
    target_template_id = templates[0]["id"]
    default_template = next((item for item in templates if item["is_default"]), None)

    get_resp = client.get(f"/api/v1/prompt-templates/{target_template_id}")
    print("GET STATUS:", get_resp.status_code)
    print("GET BODY:", get_resp.json())

    update_resp = client.put(
        f"/api/v1/prompt-templates/{target_template_id}",
        json={
            "content": "这是更新后的基础型提示词内容，用于论文原型演示。",
            "description": "更新后的演示描述",
        },
    )
    print("UPDATE STATUS:", update_resp.status_code)
    print("UPDATE BODY:", update_resp.json())

    new_default_target_id = templates[-1]["id"] if default_template and templates[-1]["id"] != default_template["id"] else templates[1]["id"]
    set_default_resp = client.put(f"/api/v1/prompt-templates/{new_default_target_id}/set-default")
    print("SET DEFAULT STATUS:", set_default_resp.status_code)
    print("SET DEFAULT BODY:", set_default_resp.json())

    final_list_resp = client.get("/api/v1/prompt-templates")
    final_templates = final_list_resp.json()
    default_count = sum(1 for item in final_templates if item["is_default"])
    final_default = next(item for item in final_templates if item["is_default"])

    print("FINAL DEFAULT COUNT:", default_count)
    print("FINAL DEFAULT TEMPLATE:", final_default)

    assert list_resp.status_code == 200
    assert len(templates) >= 3
    assert get_resp.status_code == 200
    assert update_resp.status_code == 200
    assert set_default_resp.status_code == 200
    assert default_count == 1
    assert final_default["id"] == new_default_target_id

    print("Prompt template API test completed successfully.")


if __name__ == "__main__":
    main()
