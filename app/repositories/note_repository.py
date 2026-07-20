"""Repository untuk entitas Note. Semua query difilter berdasarkan user_id."""
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repositories.base_repository import BaseRepository


class NoteRepository(BaseRepository[Note]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Note)

    async def get_by_id_for_user(self, note_id: int, user_id: int) -> Note | None:
        result = await self.session.execute(
            select(Note).where(and_(Note.id == note_id, Note.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Note]:
        result = await self.session.execute(
            select(Note).where(Note.user_id == user_id).order_by(Note.created_at.desc())
        )
        return list(result.scalars().all())
