"""Repository untuk entitas Task. Semua query difilter berdasarkan user_id (isolasi data)."""
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    async def get_by_id_for_user(self, task_id: int, user_id: int) -> Task | None:
        result = await self.session.execute(
            select(Task).where(and_(Task.id == task_id, Task.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, only_pending: bool = False) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user_id).order_by(Task.deadline.asc())
        if only_pending:
            stmt = stmt.where(Task.is_done.is_(False))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_due_for_reminder(self, upper_bound: datetime) -> list[Task]:
        """Ambil semua task (semua user) yang deadline-nya sudah dekat & belum diingatkan."""
        stmt = select(Task).where(
            and_(
                Task.is_done.is_(False),
                Task.reminder_sent.is_(False),
                Task.deadline <= upper_bound,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
