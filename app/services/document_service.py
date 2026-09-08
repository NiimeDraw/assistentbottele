"""Service penyimpanan dokumen akademik."""
from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.validators import validate_non_empty

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".ppt", ".pptx", ".zip", ".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _safe_name(value: str) -> str:
    name = Path(value).name.strip()
    name = re.sub(r"[^\w.\- ()]", "_", name, flags=re.UNICODE)
    return name[:255] or "dokumen"


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentRepository(session)

    @staticmethod
    def validate_upload(name: str, file_size: int | None) -> str:
        safe_name = _safe_name(name)
        extension = Path(safe_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValidationError(f"Format file tidak didukung. Gunakan: {allowed}.")
        max_bytes = settings.DOCUMENT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size is not None and file_size > max_bytes:
            raise ValidationError(
                f"Ukuran file maksimal {settings.DOCUMENT_MAX_FILE_SIZE_MB} MB."
            )
        return safe_name

    async def save_upload(
        self,
        bot: Bot,
        user_id: int,
        file_id: str,
        original_name: str,
        file_size: int | None,
        mime_type: str | None,
        semester: str,
        mata_kuliah: str,
        category: str,
    ) -> Document:
        original_name = self.validate_upload(original_name, file_size)
        semester = validate_non_empty(semester, "Semester", max_length=50)
        mata_kuliah = validate_non_empty(mata_kuliah, "Mata kuliah")
        category = validate_non_empty(category, "Kategori", max_length=100)

        root = Path(settings.DOCUMENT_STORAGE_PATH)
        user_directory = root / str(user_id)
        user_directory.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}{Path(original_name).suffix.lower()}"
        destination = user_directory / stored_name

        telegram_file = await bot.get_file(file_id)
        await bot.download(telegram_file, destination=destination)
        actual_size = destination.stat().st_size
        self.validate_upload(original_name, actual_size)

        document = Document(
            user_id=user_id,
            original_name=original_name,
            stored_name=stored_name,
            storage_path=str(destination),
            mime_type=mime_type,
            file_size=actual_size,
            semester=semester,
            mata_kuliah=mata_kuliah,
            category=category,
        )
        try:
            return await self.repo.add(document)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    async def list_documents(self, user_id: int, query: str | None = None) -> list[Document]:
        return await self.repo.list_by_user(user_id, query)

    async def get_document(self, document_id: int, user_id: int) -> Document:
        document = await self.repo.get_by_id_for_user(document_id, user_id)
        if not document:
            raise NotFoundError("Dokumen tidak ditemukan atau bukan milik Anda.")
        return document

    async def rename_document(self, document_id: int, user_id: int, new_name: str) -> Document:
        document = await self.get_document(document_id, user_id)
        new_name = self.validate_upload(new_name, document.file_size)
        if Path(new_name).suffix.lower() != Path(document.original_name).suffix.lower():
            raise ValidationError("Ekstensi file tidak boleh diubah saat rename.")
        document.original_name = new_name
        return document

    async def delete_document(self, document_id: int, user_id: int) -> None:
        document = await self.get_document(document_id, user_id)
        Path(document.storage_path).unlink(missing_ok=True)
        await self.repo.delete(document)
