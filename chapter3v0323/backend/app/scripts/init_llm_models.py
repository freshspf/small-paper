import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.db.base  # noqa: F401
from app.db.create_tables import create_tables
from app.db.init_models import seed_llm_models
from app.db.session import SessionLocal


def main() -> None:
    create_tables()
    with SessionLocal() as db:
        seed_llm_models(db)
    print("LLM models initialized successfully.")


if __name__ == "__main__":
    main()
