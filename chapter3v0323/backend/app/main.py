import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.db.base  # noqa: F401
from app.api.router import api_router
from app.core.config import get_settings
from app.db.base_class import Base
from app.db.create_tables import ensure_sqlite_schema
from app.db.init_model_configs import seed_model_configs
from app.db.init_models import seed_llm_models
from app.db.init_db import seed_prompt_templates
from app.db.init_prompt_template_configs import seed_prompt_template_configs
from app.db.session import SessionLocal, engine


settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    with SessionLocal() as db:
        seed_prompt_templates(db)
        seed_llm_models(db)
        seed_model_configs(db)
        seed_prompt_template_configs(db)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
