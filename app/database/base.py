"""
Base class untuk seluruh model SQLAlchemy.
Menyediakan mixin id, created_at, updated_at agar konsisten di semua tabel.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class deklaratif untuk semua model."""
    pass


class TimestampMixin:
    """Mixin kolom created_at & updated_at otomatis."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
