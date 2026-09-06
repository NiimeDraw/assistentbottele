"""Model Schedule: jadwal kuliah mingguan milik pengguna."""
from __future__ import annotations

import enum
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    # Hanya untuk type-checker (Pylance/mypy), tidak dieksekusi saat runtime.
    from app.models.user import User

class HariEnum(str, enum.Enum):
    SENIN = "Senin"
    SELASA = "Selasa"
    RABU = "Rabu"
    KAMIS = "Kamis"
    JUMAT = "Jumat"
    SABTU = "Sabtu"
    MINGGU = "Minggu"


# Pemetaan indeks weekday Python (isoweekday: Senin=1 s.d. Minggu=7) ke HariEnum
_HARI_BY_ISOWEEKDAY = (
    "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu",
)


def hari_from_date(d: date) -> HariEnum:
    """Konversi objek date ke HariEnum, terlepas dari locale server."""
    return HariEnum(_HARI_BY_ISOWEEKDAY[d.isoweekday() - 1])


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    mata_kuliah: Mapped[str] = mapped_column(String(255), nullable=False)
    hari: Mapped[HariEnum] = mapped_column(Enum(HariEnum), nullable=False)
    jam_mulai: Mapped[time] = mapped_column(Time, nullable=False)
    jam_selesai: Mapped[time] = mapped_column(Time, nullable=False)
    ruangan: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dosen dan pengaturan reminder (dalam menit sebelum jam_mulai)
    dosen: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:
        return f"<Schedule id={self.id} mata_kuliah={self.mata_kuliah!r} hari={self.hari}>"
