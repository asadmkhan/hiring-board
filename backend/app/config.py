from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://hiring:hiring@localhost:5432/hiring_board"
    frontend_origin: str = "http://localhost:5173"
    llm_mode: str = "mock"
    anthropic_api_key: SecretStr = SecretStr("")

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


settings = Settings()
