"""Model User: merepresentasikan pengguna Telegram dan profil akademik sederhana."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    # Imports for type checkers (avoid circular imports at runtime)
    from app.models.task import Task
    from app.models.schedule import Schedule
    from app.models.note import Note

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profil akademik tambahan
    fakultas: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jurusan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    angkatan: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tasks: Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notes: Mapped[List["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} username={self.username}>"
