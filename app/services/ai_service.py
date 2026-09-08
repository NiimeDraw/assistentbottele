"""Service layer untuk fitur AI Assistant melalui provider OpenAI-compatible."""
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
        provider = settings.AI_PROVIDER.strip().lower()
        if provider == "openrouter":
            api_key = settings.OPENROUTER_API_KEY
            if api_key:
                headers = {
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                    "X-Title": settings.OPENROUTER_APP_NAME,
                }
                self._client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=settings.OPENROUTER_BASE_URL,
                    default_headers={key: value for key, value in headers.items() if value},
                )
        elif provider == "openai" and settings.OPENAI_API_KEY:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def ask(self, question: str) -> str:
        if not self._client:
            raise AppError(
                "Fitur AI belum dikonfigurasi. Isi API key provider AI di file .env."
            )
        question = (question or "").strip()
        if not question:
            raise AppError("Pertanyaan tidak boleh kosong.")

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
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

    async def summarize_pdf(self, text: str, file_name: str) -> dict[str, str]:
        """Ringkas teks PDF dan kembalikan lima bagian output yang konsisten."""
        if not self._client:
            raise AppError(
                "Fitur AI belum dikonfigurasi. Isi API key provider AI di file .env."
            )
        text = (text or "").strip()
        if not text:
            raise AppError("PDF tidak memiliki teks yang bisa diringkas.")
        prompt = (
            "Ringkas dokumen PDF berikut dalam Bahasa Indonesia. Balas HANYA dengan format "
            "JSON valid tanpa markdown, dengan keys persis: "
            "short_summary, detailed_summary, key_points, important_terms, conclusion. "
            "key_points dan important_terms harus berupa array string. "
            f"Nama file: {file_name}\n\nDOKUMEN:\n{text}"
        )
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "Kamu adalah peringkas dokumen akademik yang teliti."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            import json

            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            required = {
                "short_summary", "detailed_summary", "key_points",
                "important_terms", "conclusion",
            }
            if not required.issubset(result):
                raise ValueError("Respons ringkasan tidak lengkap.")
            return {
                "short_summary": str(result["short_summary"]),
                "detailed_summary": str(result["detailed_summary"]),
                "key_points": json.dumps(result["key_points"], ensure_ascii=False),
                "important_terms": json.dumps(result["important_terms"], ensure_ascii=False),
                "conclusion": str(result["conclusion"]),
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gagal meringkas PDF")
            raise AppError("Ringkasan PDF gagal dibuat. Coba lagi nanti.") from exc

    @property
    def _model(self) -> str:
        provider = settings.AI_PROVIDER.strip().lower()
        return (
            settings.OPENROUTER_MODEL
            if provider == "openrouter"
            else settings.OPENAI_MODEL
        )
