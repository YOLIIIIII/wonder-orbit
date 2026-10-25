from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://wonder:wonder@localhost:5432/wonder"
    mock_mode: bool = True
    model_provider: Literal["openai-compatible", "bailian"] = "openai-compatible"
    model_api_base_url: str = "https://api.openai.com/v1"
    model_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    model_timeout: float = Field(default=30, gt=0, le=300)
    model_max_retries: int = Field(default=1, ge=0, le=3)
    model_max_tokens: int = Field(default=2048, ge=256, le=8192)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def effective_mock(self) -> bool:
        return self.mock_mode or not self.model_api_key


@lru_cache
def settings() -> Settings:
    return Settings()
