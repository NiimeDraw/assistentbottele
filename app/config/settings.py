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

    # AI provider (OpenRouter kompatibel dengan OpenAI API)
    AI_PROVIDER: str = "openrouter"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_NAME: str = "Campus Assistant Bot"

    # Kompatibilitas konfigurasi lama
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Scheduler
    REMINDER_CHECK_INTERVAL_MINUTES: int = 5
    REMINDER_BEFORE_MINUTES: int = 60
    REMINDER_SEND_RETRIES: int = 2
    REMINDER_RETRY_DELAY_SECONDS: float = 2.0

    # Penyimpanan dokumen
    DOCUMENT_STORAGE_PATH: str = "storage/documents"
    DOCUMENT_MAX_FILE_SIZE_MB: int = 20
    PDF_SUMMARY_STORAGE_PATH: str = "storage/pdf_summaries"
    PDF_SUMMARY_RETENTION_HOURS: int = 1
    PDF_SUMMARY_CHUNK_PAGES: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def validate_required_settings() -> None:
    """Fail fast dengan pesan jelas jika konfigurasi minimum belum tersedia."""
    missing = [
        name
        for name, value in (
            ("BOT_TOKEN", settings.BOT_TOKEN),
            ("DATABASE_URL", settings.DATABASE_URL),
        )
        if not value.strip()
    ]
    if missing:
        raise RuntimeError(
            "Konfigurasi wajib belum diisi: "
            + ", ".join(missing)
            + ". Isi variabel tersebut di file .env."
        )
