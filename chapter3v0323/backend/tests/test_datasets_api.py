import io
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.create_tables import create_tables
from app.db.session import SessionLocal
from app.main import app
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord


def reset_dataset_tables() -> None:
    with SessionLocal() as db:
        db.query(DatasetRecord).delete()
        db.query(Dataset).delete()
        db.commit()


def build_csv_bytes() -> bytes:
    lines = [
        "id,axiom_type,axiom_text,subject,predicate,object,label,source,context_info",
    ]
    for index in range(1, 26):
        lines.append(
            f"sample_{index},subClassOf,Axiom {index},Subject{index},predicate_{index},Object{index},1,demo_source,Context {index}"
        )
    return "\n".join(lines).encode("utf-8")


def main() -> None:
    create_tables()
    reset_dataset_tables()

    client = TestClient(app)

    create_resp = client.post(
        "/api/v1/datasets",
        json={
            "name": "演示数据集",
            "description": "用于论文第五章演示",
            "source": "manual",
        },
    )
    print("CREATE DATASET STATUS:", create_resp.status_code)
    print("CREATE DATASET BODY:", create_resp.json())

    upload_resp = client.post(
        "/api/v1/datasets/upload",
        data={
            "name": "CSV 演示数据集",
            "description": "CSV 上传测试",
            "source": "csv_demo",
        },
        files={
            "file": ("demo_dataset.csv", io.BytesIO(build_csv_bytes()), "text/csv"),
        },
    )
    print("UPLOAD STATUS:", upload_resp.status_code)
    print("UPLOAD BODY:", upload_resp.json())

    dataset_id = upload_resp.json()["id"]

    list_resp = client.get("/api/v1/datasets")
    print("LIST STATUS:", list_resp.status_code)
    print("LIST SIZE:", len(list_resp.json()))

    detail_resp = client.get(f"/api/v1/datasets/{dataset_id}")
    print("DETAIL STATUS:", detail_resp.status_code)
    print("DETAIL BODY:", detail_resp.json())

    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview")
    print("PREVIEW STATUS:", preview_resp.status_code)
    print("PREVIEW SIZE:", len(preview_resp.json()))
    print("PREVIEW FIRST ROW:", preview_resp.json()[0])

    assert create_resp.status_code == 201
    assert upload_resp.status_code == 201
    assert list_resp.status_code == 200
    assert detail_resp.status_code == 200
    assert preview_resp.status_code == 200
    assert len(preview_resp.json()) == 20

    print("Dataset API test completed successfully.")


if __name__ == "__main__":
    main()
