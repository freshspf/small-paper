from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
LEGACY_RESOURCE_DIR = BASE_DIR.parent / "chapter3"


class Settings(BaseSettings):
    app_name: str = "RDFS Ontology Learning and Evaluation System"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        default=f"sqlite:///{(BASE_DIR / 'app.db').as_posix()}",
        alias="DATABASE_URL",
    )
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env",
            BASE_DIR / ".env.local",
            LEGACY_RESOURCE_DIR / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def normalized_database_url(self) -> str:
        if not self.database_url.startswith("sqlite:///"):
            return self.database_url

        sqlite_path = self.database_url.replace("sqlite:///", "", 1)
        path = Path(sqlite_path)
        if path.is_absolute():
            return self.database_url

        normalized_path = (BASE_DIR.parent / path).resolve()
        return f"sqlite:///{normalized_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
