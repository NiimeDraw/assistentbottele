"""Service layer untuk fitur Tugas (Task). Berisi validasi & aturan bisnis."""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.utils.exceptions import NotFoundError
from app.utils.validators import validate_deadline, validate_non_empty


class TaskService:
    def __init__(self, session: AsyncSession):
        self.repo = TaskRepository(session)

    async def create_task(
        self, user_id: int, title: str, deadline_raw: str, description: str | None = None
    ) -> Task:
        title = validate_non_empty(title, "Judul tugas")
        deadline = validate_deadline(deadline_raw)
        task = Task(
            user_id=user_id,
            title=title,
            description=(description or "").strip() or None,
            deadline=deadline,
        )
        return await self.repo.add(task)

    async def list_tasks(self, user_id: int, only_pending: bool = False) -> list[Task]:
        return await self.repo.list_by_user(user_id, only_pending=only_pending)

    async def get_task(self, task_id: int, user_id: int) -> Task:
        task = await self.repo.get_by_id_for_user(task_id, user_id)
        if not task:
            raise NotFoundError("Tugas tidak ditemukan atau bukan milik Anda.")
        return task

    async def mark_done(self, task_id: int, user_id: int) -> Task:
        task = await self.get_task(task_id, user_id)
        task.is_done = True
        return task

    async def delete_task(self, task_id: int, user_id: int) -> None:
        task = await self.get_task(task_id, user_id)
        await self.repo.delete(task)

    async def list_due_for_reminder(self, upper_bound: datetime) -> list[Task]:
        return await self.repo.list_due_for_reminder(upper_bound)
