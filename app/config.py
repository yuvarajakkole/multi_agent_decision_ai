# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

settings = Settings()

print("CONFIG LOADED | OPENAI_API_KEY =", settings.OPENAI_API_KEY[:12])
