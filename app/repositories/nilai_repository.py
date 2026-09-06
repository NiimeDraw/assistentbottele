"""Repository untuk entitas Nilai."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nilai import Nilai
from app.repositories.base_repository import BaseRepository


class NilaiRepository(BaseRepository[Nilai]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Nilai)

    async def list_by_user(
        self, user_id: int, semester: int | None = None
    ) -> list[Nilai]:
        """Ambil semua nilai milik user, opsional filter per semester."""
        stmt = select(Nilai).where(Nilai.user_id == user_id)
        if semester is not None:
            stmt = stmt.where(Nilai.semester == semester)
        stmt = stmt.order_by(Nilai.semester, Nilai.mata_kuliah)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_semesters(self, user_id: int) -> list[int]:
        """Ambil daftar semester yang sudah memiliki data nilai."""
        stmt = (
            select(Nilai.semester)
            .where(Nilai.user_id == user_id)
            .distinct()
            .order_by(Nilai.semester)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ips(self, user_id: int, semester: int) -> float | None:
        """Hitung IPS (Indeks Prestasi Semester) untuk semester tertentu.

        IPS = Σ(nilai × SKS) / Σ(SKS)
        """
        stmt = (
            select(
                func.sum(Nilai.nilai * Nilai.sks).label("total_bobot"),
                func.sum(Nilai.sks).label("total_sks"),
            )
            .where(Nilai.user_id == user_id, Nilai.semester == semester)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None or row.total_sks is None or row.total_sks == 0:
            return None
        return round(float(row.total_bobot) / float(row.total_sks), 2)

    async def get_ipk(self, user_id: int) -> float | None:
        """Hitung IPK (Indeks Prestasi Kumulatif) seluruh semester.

        IPK = Σ(nilai × SKS) seluruh semester / Σ(SKS) seluruh semester
        """
        stmt = (
            select(
                func.sum(Nilai.nilai * Nilai.sks).label("total_bobot"),
                func.sum(Nilai.sks).label("total_sks"),
            )
            .where(Nilai.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None or row.total_sks is None or row.total_sks == 0:
            return None
        return round(float(row.total_bobot) / float(row.total_sks), 2)

    async def get_total_sks(self, user_id: int) -> int:
        """Total SKS yang sudah diambil."""
        stmt = (
            select(func.sum(Nilai.sks))
            .where(Nilai.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        total = result.scalar()
        return int(total) if total else 0

    async def get_by_user_and_id(
        self, user_id: int, nilai_id: int
    ) -> Nilai | None:
        """Ambil satu nilai berdasarkan user_id dan id."""
        stmt = select(Nilai).where(
            Nilai.user_id == user_id, Nilai.id == nilai_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
