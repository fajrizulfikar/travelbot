from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_VERSION: str = "0.1.0"
    LLM_PROVIDER: str = "claude"
    CLAUDE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    VECTOR_STORE_BACKEND: str = "chroma"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CONFIDENCE_THRESHOLD: float = 0.60
    SIMILARITY_THRESHOLD: float = 0.70
    TOP_N_RESULTS: int = 5
    MAX_FILE_SIZE_MB: int = 50
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
