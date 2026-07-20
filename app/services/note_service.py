"""Service layer untuk fitur Catatan (Note)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.utils.exceptions import NotFoundError
from app.utils.validators import validate_non_empty


class NoteService:
    def __init__(self, session: AsyncSession):
        self.repo = NoteRepository(session)

    async def create_note(self, user_id: int, title: str, content: str) -> Note:
        title = validate_non_empty(title, "Judul catatan")
        content = validate_non_empty(content, "Isi catatan", max_length=4000)
        note = Note(user_id=user_id, title=title, content=content)
        return await self.repo.add(note)

    async def list_notes(self, user_id: int) -> list[Note]:
        return await self.repo.list_by_user(user_id)

    async def get_note(self, note_id: int, user_id: int) -> Note:
        note = await self.repo.get_by_id_for_user(note_id, user_id)
        if not note:
            raise NotFoundError("Catatan tidak ditemukan atau bukan milik Anda.")
        return note

    async def delete_note(self, note_id: int, user_id: int) -> None:
        note = await self.get_note(note_id, user_id)
        await self.repo.delete(note)
