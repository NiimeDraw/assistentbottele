"""Service layer untuk User: menjembatani handler dengan repository."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def get_or_create_user(self, telegram_id: int, full_name: str, username: str | None) -> User:
        return await self.repo.get_or_create(telegram_id, full_name, username)

    async def update_profile(self, user_id: int, **kwargs) -> User:
        return await self.repo.update_profile(user_id, **kwargs)

    async def delete_user_by_telegram_id(self, telegram_id: int) -> None:
        return await self.repo.delete_by_telegram_id(telegram_id)
