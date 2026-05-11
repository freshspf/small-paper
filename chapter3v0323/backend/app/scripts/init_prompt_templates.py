import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import seed_prompt_templates
from app.db.session import SessionLocal
import app.db.base  # noqa: F401


def main() -> None:
    with SessionLocal() as db:
        seed_prompt_templates(db)
    print("Prompt templates initialized successfully.")


if __name__ == "__main__":
    main()
