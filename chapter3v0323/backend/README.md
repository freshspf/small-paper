# Backend Skeleton

## Run

1. Copy `.env.example` to `.env`:

```bash
cp backend/.env.example backend/.env
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Choose database:

MySQL recommended:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/chapter3v0323?charset=utf8mb4
```

SQLite fallback:

```env
DATABASE_URL=sqlite:///./backend/app.db
```

4. Start the API:

```bash
uvicorn app.main:app --app-dir backend --reload
```

Or run directly:

```bash
python backend/app/main.py
```

## Test LLM Model APIs

Run the minimal CRUD verification script:

```bash
python backend/tests/test_llm_models_api.py
```

## Included

- FastAPI application skeleton
- SQLAlchemy database connection with MySQL or SQLite
- Pydantic schemas
- App directory structure
- `/health` interface
- Auto-created local SQLite database file `backend/app.db` when using SQLite
- Core tables for models, datasets, dataset records, prompt templates, evaluation jobs, evaluation results, and explanation annotations
- Built-in prompt template seeding
- Basic CRUD APIs for models, datasets, and prompt templates
- CSV/JSON dataset upload and ingestion

## MySQL Notes

- Recommended driver: `mysql+pymysql`
- Create the database first, for example:

```sql
CREATE DATABASE chapter3v0323 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- Then start the backend. Tables will be created automatically on startup.
- `ensure_sqlite_schema()` only applies SQLite-specific compatibility fixes and is skipped automatically for MySQL.
