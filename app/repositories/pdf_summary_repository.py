"""Repository histori ringkasan PDF."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pdf_summary import PdfSummary
from app.repositories.base_repository import BaseRepository


class PdfSummaryRepository(BaseRepository[PdfSummary]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PdfSummary)

    async def list_by_user(self, user_id: int) -> list[PdfSummary]:
        result = await self.session.execute(
            select(PdfSummary)
            .where(PdfSummary.user_id == user_id)
            .order_by(PdfSummary.created_at.desc())
        )
        return list(result.scalars().all())
