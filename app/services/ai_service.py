"""Service layer untuk fitur AI Assistant (Tanya AI) menggunakan OpenAI API."""
from openai import AsyncOpenAI

from app.config.settings import settings
from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Kamu adalah asisten akademik untuk mahasiswa Indonesia bernama Campus Assistant. "
    "Jawab pertanyaan seputar akademik, tugas kuliah, dan produktivitas secara singkat, "
    "jelas, dan dalam Bahasa Indonesia yang sopan."
)


class AIService:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.OPENAI_API_KEY:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def ask(self, question: str) -> str:
        if not self._client:
            raise AppError(
                "Fitur AI belum dikonfigurasi. Admin bot perlu mengisi OPENAI_API_KEY di .env"
            )
        question = (question or "").strip()
        if not question:
            raise AppError("Pertanyaan tidak boleh kosong.")

        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                max_tokens=800,
            )
            return response.choices[0].message.content or "Maaf, AI tidak memberikan jawaban."
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gagal memanggil OpenAI API")
            raise AppError("Terjadi kesalahan saat menghubungi layanan AI. Coba lagi nanti.") from exc
