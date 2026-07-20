"""
Repository dasar generik.
Semua repository spesifik mewarisi class ini untuk operasi CRUD umum.
"""
from typing import Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        return await self.session.get(self.model, obj_id)

    async def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def list_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())
