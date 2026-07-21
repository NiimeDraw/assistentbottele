"""Model AcademicEvent: event kalender akademik (UTS, UAS, KRS, KHS, Libur, Wisuda, Seminar)."""
from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    # Hanya untuk type-checker (Pylance/mypy), tidak dieksekusi saat runtime.
    # Menghindari circular import karena User juga mereferensikan AcademicEvent.
    from app.models.user import User


class EventTypeEnum(str, enum.Enum):
    UTS = "UTS"
    UAS = "UAS"
    KRS = "KRS"
    KHS = "KHS"
    LIBUR = "Libur"
    WISUDA = "Wisuda"
    SEMINAR = "Seminar"
    LAINNYA = "Lainnya"


# Emoji penanda tiap jenis event, dipakai di tampilan list & detail
EVENT_TYPE_EMOJI: dict[EventTypeEnum, str] = {
    EventTypeEnum.UTS: "📝",
    EventTypeEnum.UAS: "📕",
    EventTypeEnum.KRS: "🗂️",
    EventTypeEnum.KHS: "📊",
    EventTypeEnum.LIBUR: "🏖️",
    EventTypeEnum.WISUDA: "🎓",
    EventTypeEnum.SEMINAR: "🎤",
    EventTypeEnum.LAINNYA: "📌",
}


class AcademicEvent(Base, TimestampMixin):
    __tablename__ = "academic_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[EventTypeEnum] = mapped_column(Enum(EventTypeEnum), nullable=False, index=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # None = tanpa pengingat. Kalau diisi, artinya "ingatkan N hari sebelum start_date".
    reminder_days_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="academic_events")

    def __repr__(self) -> str:
        return f"<AcademicEvent id={self.id} title={self.title!r} type={self.event_type}>"