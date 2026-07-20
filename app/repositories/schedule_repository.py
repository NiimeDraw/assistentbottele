"""Repository untuk entitas Schedule. Semua query difilter berdasarkan user_id."""
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Schedule)

    async def get_by_id_for_user(self, schedule_id: int, user_id: int) -> Schedule | None:
        result = await self.session.execute(
            select(Schedule).where(and_(Schedule.id == schedule_id, Schedule.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).where(Schedule.user_id == user_id).order_by(Schedule.jam_mulai.asc())
        )
        return list(result.scalars().all())
