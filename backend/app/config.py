from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://hiring:hiring@localhost:5432/hiring_board"
    frontend_origin: str = "http://localhost:5173"

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]

    # Scoring providers.
    anthropic_api_key: SecretStr = SecretStr("")
    claude_model: str = "claude-haiku-4-5"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-6-luna"
    ollama_url: str = ""
    ollama_model: str = "llama3.2:3b"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


settings = Settings()
