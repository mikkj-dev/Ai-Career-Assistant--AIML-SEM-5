from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql://groundup:groundup@localhost:5433/groundup"
    jwt_secret: str = "dev-only-groundup-signing-key-rotate-in-production"
    jwt_ttl_days: int = 7
    google_client_id: str = ""
    cors_origins: str = "http://localhost:3000"
    demo_enabled: bool = False
    similarity_method: Literal["tfidf", "sentence-bert"] = "tfidf"
    sentence_bert_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    evaluation_dir: Path = Path(__file__).resolve().parents[2] / "evaluation"

    @property
    def local_demo(self) -> bool:
        return self.env == "development" and self.demo_enabled

    @property
    def sqlalchemy_url(self) -> str:
        # Neon/Render hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the driver named.
        url = self.database_url.replace("postgres://", "postgresql://", 1)
        return url.replace("postgresql://", "postgresql+psycopg://", 1)


settings = Settings()

if settings.env == "production" and (
    len(settings.jwt_secret.encode()) < 32 or settings.jwt_secret.startswith("dev-only-")
):
    raise RuntimeError("Production JWT_SECRET must be at least 32 bytes and differ from the development key")
