"""
Manajemen koneksi & session database (async) menggunakan SQLAlchemy 2.x.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings

# Lazily initialize engine and session factory to avoid requiring DB driver at import time
_engine: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker | None = None


def _init_db():
    """Inisialisasi engine dan AsyncSessionFactory kalau belum ada.
    Ini memastikan import modul tidak gagal jika driver DB belum terpasang.
    """
    global _engine, AsyncSessionFactory
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
        AsyncSessionFactory = async_sessionmaker(
            bind=_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager untuk mendapatkan session database async.

    Memanggil _init_db() pada pemanggilan pertama sehingga impor modul tidak langsung
    membutuhkan driver database (mis. psycopg).
    """
    _init_db()
    assert AsyncSessionFactory is not None
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
