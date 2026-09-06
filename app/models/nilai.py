"""Model Nilai: nilai mata kuliah per semester milik pengguna."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Nilai(Base, TimestampMixin):
    __tablename__ = "nilai"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mata_kuliah: Mapped[str] = mapped_column(String(255), nullable=False)
    sks: Mapped[int] = mapped_column(Integer, nullable=False)
    nilai: Mapped[float] = mapped_column(Float, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="nilai_list")

    @property
    def nilai_huruf(self) -> str:
        """Konversi nilai angka ke huruf (standar Indonesia 4.0 scale)."""
        if self.nilai >= 4.0:
            return "A"
        elif self.nilai >= 3.7:
            return "A-"
        elif self.nilai >= 3.3:
            return "B+"
        elif self.nilai >= 3.0:
            return "B"
        elif self.nilai >= 2.7:
            return "B-"
        elif self.nilai >= 2.3:
            return "C+"
        elif self.nilai >= 2.0:
            return "C"
        elif self.nilai >= 1.7:
            return "C-"
        elif self.nilai >= 1.0:
            return "D"
        else:
            return "E"

    @property
    def bobot(self) -> float:
        """Bobot nilai = nilai × SKS."""
        return self.nilai * self.sks

    def __repr__(self) -> str:
        return (
            f"<Nilai id={self.id} mk={self.mata_kuliah!r} "
            f"semester={self.semester} nilai={self.nilai}>"
        )
