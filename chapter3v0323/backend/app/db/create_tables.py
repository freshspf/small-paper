import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text

from app.db.base_class import Base
from app.db.session import engine
import app.db.base  # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    ensure_ontology_task_schema()


def ensure_sqlite_schema() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "llm_models" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("llm_models")}
        if "is_default" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE llm_models ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT 0"))

    if "datasets" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("datasets")}
        if "has_labels" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE datasets ADD COLUMN has_labels BOOLEAN NOT NULL DEFAULT 0"))

    if "prompt_templates" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("prompt_templates")}
        if "is_default" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE prompt_templates ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT 0"))

    if "evaluation_results" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("evaluation_results")}
        if "raw_response" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE evaluation_results ADD COLUMN raw_response TEXT"))


def ensure_ontology_task_schema() -> None:
    inspector = inspect(engine)
    if "ontology_task" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("ontology_task")}
    long_text = "LONGTEXT" if engine.dialect.name == "mysql" else "TEXT"
    additions = {
        "executionMode": "VARCHAR(50)",
        "semanticPromptId": "INTEGER",
        "termPromptId": "INTEGER",
        "conceptPromptId": "INTEGER",
        "domainSwitch": "INTEGER NOT NULL DEFAULT 0",
        "chunkMetadataSwitch": "INTEGER NOT NULL DEFAULT 1",
        "inputType": "VARCHAR(20)",
        "fileName": "VARCHAR(255)",
        "filePath": "VARCHAR(500)",
        "totalChunkCount": "INTEGER NOT NULL DEFAULT 0",
        "successCount": "INTEGER NOT NULL DEFAULT 0",
        "failCount": "INTEGER NOT NULL DEFAULT 0",
        "mergedOutput": long_text,
    }
    with engine.begin() as conn:
        for column_name, column_type in additions.items():
            if column_name not in columns:
                conn.execute(text(f"ALTER TABLE ontology_task ADD COLUMN {column_name} {column_type}"))
        if engine.dialect.name == "mysql" and "inputText" in columns:
            conn.execute(text("ALTER TABLE ontology_task MODIFY COLUMN inputText LONGTEXT NULL"))

    if "ontology_chunk_result" in inspector.get_table_names():
        result_columns = {column["name"] for column in inspector.get_columns("ontology_chunk_result")}
        if "layerName" not in result_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE ontology_chunk_result ADD COLUMN layerName VARCHAR(50)"))


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
