"""Repository untuk entitas User."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        full_name: str,
        username: str | None,
        fakultas: str | None = None,
        jurusan: str | None = None,
        angkatan: int | None = None,
        semester: int | None = None,
    ) -> User:
        """Ambil user berdasarkan telegram_id atau buat baru. Jika field profil diberikan, perbarui ketika berbeda."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            updated = False
            if user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if user.username != username:
                user.username = username
                updated = True

            # Perbarui profiling jika nilai eksplisit diberikan
            if fakultas is not None and user.fakultas != fakultas:
                user.fakultas = fakultas
                updated = True
            if jurusan is not None and user.jurusan != jurusan:
                user.jurusan = jurusan
                updated = True
            if angkatan is not None and user.angkatan != angkatan:
                user.angkatan = angkatan
                updated = True
            if semester is not None and user.semester != semester:
                user.semester = semester
                updated = True

            if updated:
                await self.session.flush()
            return user

        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            fakultas=fakultas,
            jurusan=jurusan,
            angkatan=angkatan,
            semester=semester,
        )
        return await self.add(user)

    async def update_profile(self, user_id: int, **kwargs) -> User:
        """Perbarui profil user (only allowed fields)."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        allowed = {"full_name", "username", "fakultas", "jurusan", "angkatan", "semester"}
        updated = False
        for k, v in kwargs.items():
            if k in allowed and getattr(user, k) != v:
                setattr(user, k, v)
                updated = True
        if updated:
            await self.session.flush()
        return user

    async def delete_by_telegram_id(self, telegram_id: int) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            await self.delete(user)
