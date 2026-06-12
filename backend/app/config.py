from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "postgresql://archagent:archagent@localhost:5432/archagent"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Data directory (override via env: ARCHAGENT_DATA_DIR=/app/data)
    data_dir: str = "data"

    # Reward model settings
    cold_start_threshold: int = 20  # Min annotations before model activates
    confidence_high: float = 0.7
    confidence_low: float = 0.4

    # LLM settings
    llm_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    @property
    def reward_model_path(self) -> str:
        return str(Path(self.data_dir) / "reward_model.joblib")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()