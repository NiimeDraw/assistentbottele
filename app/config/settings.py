"""
Konfigurasi aplikasi.
Membaca variabel environment (.env) menggunakan pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = ""

    # Database
    DATABASE_URL: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Scheduler
    REMINDER_CHECK_INTERVAL_MINUTES: int = 5
    REMINDER_BEFORE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
