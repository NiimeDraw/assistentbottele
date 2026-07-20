"""Repository untuk entitas AcademicEvent. Semua query difilter berdasarkan user_id (isolasi data)."""
from datetime import date

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_event import AcademicEvent
from app.repositories.base_repository import BaseRepository


class AcademicEventRepository(BaseRepository[AcademicEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AcademicEvent)

    async def get_by_id_for_user(self, event_id: int, user_id: int) -> AcademicEvent | None:
        result = await self.session.execute(
            select(AcademicEvent).where(
                and_(AcademicEvent.id == event_id, AcademicEvent.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[AcademicEvent]:
        result = await self.session.execute(
            select(AcademicEvent)
            .where(AcademicEvent.user_id == user_id)
            .order_by(AcademicEvent.start_date.asc())
        )
        return list(result.scalars().all())

    async def list_by_month(self, user_id: int, year: int, month: int) -> list[AcademicEvent]:
        """Ambil event yang start_date-nya jatuh di bulan & tahun tertentu."""
        result = await self.session.execute(
            select(AcademicEvent)
            .where(
                and_(
                    AcademicEvent.user_id == user_id,
                    extract("year", AcademicEvent.start_date) == year,
                    extract("month", AcademicEvent.start_date) == month,
                )
            )
            .order_by(AcademicEvent.start_date.asc())
        )
        return list(result.scalars().all())

    async def search(self, user_id: int, keyword: str) -> list[AcademicEvent]:
        """Cari event berdasarkan judul (case-insensitive, partial match)."""
        result = await self.session.execute(
            select(AcademicEvent)
            .where(
                and_(
                    AcademicEvent.user_id == user_id,
                    AcademicEvent.title.ilike(f"%{keyword}%"),
                )
            )
            .order_by(AcademicEvent.start_date.asc())
        )
        return list(result.scalars().all())

    async def list_pending_reminders(self, today: date) -> list[AcademicEvent]:
        """
        Ambil semua event (semua user) yang punya reminder aktif, belum terkirim,
        dan tanggal mulainya belum lewat. Filter presisi "sudah waktunya diingatkan
        atau belum" (berdasarkan reminder_days_before per-event) dilakukan di service,
        karena itu perhitungan tanggal dinamis per baris yang lebih mudah & jelas di Python
        daripada di level SQL.
        """
        result = await self.session.execute(
            select(AcademicEvent).where(
                and_(
                    AcademicEvent.reminder_days_before.is_not(None),
                    AcademicEvent.reminder_sent.is_(False),
                    AcademicEvent.start_date >= today,
                )
            )
        )
        return list(result.scalars().all())