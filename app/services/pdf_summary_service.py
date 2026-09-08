"""Pipeline download, ekstraksi, chunking, dan histori ringkasan PDF."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.pdf_summary import PdfSummary
from app.repositories.pdf_summary_repository import PdfSummaryRepository
from app.services.ai_service import AIService
from app.utils.exceptions import AppError, ValidationError


class PdfSummaryService:
    def __init__(self, session: AsyncSession):
        self.repo = PdfSummaryRepository(session)

    async def summarize_upload(
        self,
        bot: Bot,
        user_id: int,
        file_id: str,
        file_name: str,
        file_size: int | None,
    ) -> PdfSummary:
        if not file_name.lower().endswith(".pdf"):
            raise ValidationError("File ringkasan harus berformat PDF.")
        max_bytes = settings.DOCUMENT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size and file_size > max_bytes:
            raise ValidationError(
                f"Ukuran PDF maksimal {settings.DOCUMENT_MAX_FILE_SIZE_MB} MB."
            )

        root = Path(settings.PDF_SUMMARY_STORAGE_PATH) / str(user_id)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{uuid4().hex}.pdf"
        try:
            telegram_file = await bot.get_file(file_id)
            await bot.download(telegram_file, destination=path)
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            if not any(page.strip() for page in pages):
                raise AppError("PDF tidak memiliki teks yang dapat diekstrak.")

            chunks = self._chunks(pages)
            ai = AIService()
            if len(chunks) == 1:
                result = await ai.summarize_pdf(chunks[0], file_name)
            else:
                partials = []
                for index, chunk in enumerate(chunks, start=1):
                    partial = await ai.summarize_pdf(
                        chunk, f"{file_name} - bagian {index}/{len(chunks)}"
                    )
                    partials.append(
                        "\n".join(
                            [
                                partial["short_summary"],
                                partial["detailed_summary"],
                                partial["key_points"],
                                partial["important_terms"],
                                partial["conclusion"],
                            ]
                        )
                    )
                result = await ai.summarize_pdf(
                    "\n\n".join(partials), file_name
                )

            downloaded_at = datetime.now(timezone.utc)
            summary = PdfSummary(
                user_id=user_id,
                file_name=Path(file_name).name[:255],
                page_count=len(pages),
                downloaded_at=downloaded_at,
                file_expires_at=downloaded_at
                + timedelta(hours=settings.PDF_SUMMARY_RETENTION_HOURS),
                **result,
            )
            saved = await self.repo.add(summary)
            return saved
        except Exception:
            path.unlink(missing_ok=True)
            raise

    @staticmethod
    async def cleanup_expired_files() -> None:
        """Hapus PDF sementara setelah melewati masa retensi konfigurasi."""
        root = Path(settings.PDF_SUMMARY_STORAGE_PATH)
        if not root.exists():
            return
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=settings.PDF_SUMMARY_RETENTION_HOURS
        )
        for path in root.rglob("*.pdf"):
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            if modified_at <= cutoff:
                path.unlink(missing_ok=True)

    @staticmethod
    def _chunks(pages: list[str]) -> list[str]:
        size = settings.PDF_SUMMARY_CHUNK_PAGES if len(pages) > 100 else len(pages)
        return [
            "\n\n".join(pages[index : index + size])
            for index in range(0, len(pages), size)
        ]

    async def list_history(self, user_id: int) -> list[PdfSummary]:
        return await self.repo.list_by_user(user_id)

    @staticmethod
    def format_history(summary: PdfSummary) -> str:
        return (
            f"📄 <b>{summary.file_name}</b> ({summary.page_count} halaman)\n\n"
            f"<b>Ringkasan Singkat</b>\n{summary.short_summary}\n\n"
            f"<b>Ringkasan Detail</b>\n{summary.detailed_summary}\n\n"
            f"<b>Poin Penting</b>\n{_format_json_list(summary.key_points)}\n\n"
            f"<b>Istilah Penting</b>\n{_format_json_list(summary.important_terms)}\n\n"
            f"<b>Kesimpulan</b>\n{summary.conclusion}"
        )


def _format_json_list(value: str) -> str:
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return value
    return "\n".join(f"• {item}" for item in items)
