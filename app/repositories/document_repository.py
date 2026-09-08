"""Repository dokumen dengan isolasi data berdasarkan pengguna."""
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def get_by_id_for_user(self, document_id: int, user_id: int) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, query: str | None = None) -> list[Document]:
        statement = select(Document).where(Document.user_id == user_id)
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Document.original_name.ilike(pattern),
                    Document.semester.ilike(pattern),
                    Document.mata_kuliah.ilike(pattern),
                    Document.category.ilike(pattern),
                )
            )
        result = await self.session.execute(
            statement.order_by(
                Document.semester, Document.mata_kuliah, Document.category, Document.original_name
            )
        )
        return list(result.scalars().all())
