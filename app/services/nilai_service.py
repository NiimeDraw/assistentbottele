"""Service layer untuk fitur Nilai & IPK Calculator."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nilai import Nilai
from app.repositories.nilai_repository import NilaiRepository
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.validators import validate_non_empty


class NilaiService:
    def __init__(self, session: AsyncSession):
        self.repo = NilaiRepository(session)

    # ── CRUD ──────────────────────────────────────────────

    async def add_nilai(
        self,
        user_id: int,
        mata_kuliah: str,
        sks: int,
        nilai: float,
        semester: int,
    ) -> Nilai:
        mata_kuliah = validate_non_empty(mata_kuliah, "Mata kuliah")
        if sks <= 0:
            raise ValidationError("SKS harus lebih dari 0.")
        if nilai < 0 or nilai > 4.0:
            raise ValidationError("Nilai harus antara 0.00 – 4.00.")
        if semester <= 0:
            raise ValidationError("Semester harus lebih dari 0.")

        entry = Nilai(
            user_id=user_id,
            mata_kuliah=mata_kuliah,
            sks=sks,
            nilai=nilai,
            semester=semester,
        )
        return await self.repo.add(entry)

    async def list_nilai(
        self, user_id: int, semester: int | None = None
    ) -> list[Nilai]:
        return await self.repo.list_by_user(user_id, semester=semester)

    async def get_nilai(self, user_id: int, nilai_id: int) -> Nilai:
        entry = await self.repo.get_by_user_and_id(user_id, nilai_id)
        if not entry:
            raise NotFoundError("Data nilai tidak ditemukan.")
        return entry

    async def delete_nilai(self, user_id: int, nilai_id: int) -> None:
        entry = await self.get_nilai(user_id, nilai_id)
        await self.repo.delete(entry)

    async def get_semesters(self, user_id: int) -> list[int]:
        return await self.repo.get_semesters(user_id)

    # ── IPS & IPK ─────────────────────────────────────────

    async def hitung_ips(self, user_id: int, semester: int) -> dict:
        """Hitung IPS untuk satu semester."""
        nilai_list = await self.repo.list_by_user(user_id, semester)
        if not nilai_list:
            raise NotFoundError(f"Tidak ada data nilai untuk semester {semester}.")

        total_sks = sum(n.sks for n in nilai_list)
        total_bobot = sum(n.bobot for n in nilai_list)
        ips = round(total_bobot / total_sks, 2)

        return {
            "semester": semester,
            "ips": ips,
            "total_sks": total_sks,
            "total_bobot": round(total_bobot, 2),
            "jumlah_mk": len(nilai_list),
        }

    async def hitung_ipk(self, user_id: int) -> dict:
        """Hitung IPK kumulatif seluruh semester."""
        ipk = await self.repo.get_ipk(user_id)
        if ipk is None:
            raise NotFoundError("Belum ada data nilai. Silakan tambahkan nilai terlebih dahulu.")

        total_sks = await self.repo.get_total_sks(user_id)
        semesters = await self.repo.get_semesters(user_id)

        # Hitung IPS per semester untuk riwayat
        riwayat = []
        for sem in semesters:
            ips_data = await self.hitung_ips(user_id, sem)
            riwayat.append(ips_data)

        return {
            "ipk": ipk,
            "total_sks": total_sks,
            "jumlah_semester": len(semesters),
            "riwayat": riwayat,
        }

    # ── Target IPK ────────────────────────────────────────

    async def hitung_target_ipk(
        self, user_id: int, target_ipk: float, sisa_sks: int
    ) -> dict:
        """Hitung rata-rata nilai yang harus dicapai di sisa SKS
        untuk mencapai target IPK.

        Rumus:
          IPK_target = (IPK_sekarang × SKS_sekarang + X × sisa_sks) / (SKS_sekarang + sisa_sks)
          X = (IPK_target × (SKS_sekarang + sisa_sks) - IPK_sekarang × SKS_sekarang) / sisa_sks
        """
        if target_ipk < 0 or target_ipk > 4.0:
            raise ValidationError("Target IPK harus antara 0.00 – 4.00.")
        if sisa_sks <= 0:
            raise ValidationError("Sisa SKS harus lebih dari 0.")

        ipk_sekarang = await self.repo.get_ipk(user_id)
        if ipk_sekarang is None:
            raise NotFoundError("Belum ada data nilai. Silakan tambahkan nilai terlebih dahulu.")

        sks_sekarang = await self.repo.get_total_sks(user_id)
        total_sks_nanti = sks_sekarang + sisa_sks

        # Nilai rata-rata yang dibutuhkan
        required_avg = (
            (target_ipk * total_sks_nanti) - (ipk_sekarang * sks_sekarang)
        ) / sisa_sks

        feasible = required_avg <= 4.0

        return {
            "ipk_sekarang": ipk_sekarang,
            "sks_sekarang": sks_sekarang,
            "target_ipk": target_ipk,
            "sisa_sks": sisa_sks,
            "total_sks_nanti": total_sks_nanti,
            "required_avg": round(max(required_avg, 0), 2),
            "feasible": feasible,
            "message": (
                f"✅ Mungkin! Anda perlu rata-rata {round(required_avg, 2)} per SKS."
                if feasible
                else f"❌ Tidak mungkin. Dibutuhkan rata-rata {round(required_avg, 2)} (> 4.00)."
            ),
        }

    # ── Prediksi IPK ──────────────────────────────────────

    async def prediksi_ipk(
        self,
        user_id: int,
        rencana: list[dict],
    ) -> dict:
        """Prediksi IPK setelah menambahkan rencana nilai.

        rencana: list of {"mata_kuliah": str, "sks": int, "prediksi_nilai": float}
        """
        ipk_sekarang = await self.repo.get_ipk(user_id)
        sks_sekarang = await self.repo.get_total_sks(user_id)

        if ipk_sekarang is None:
            ipk_sekarang = 0.0
            sks_sekarang = 0

        tambahan_sks = sum(item["sks"] for item in rencana)
        tambahan_bobot = sum(item["sks"] * item["prediksi_nilai"] for item in rencana)

        total_sks = sks_sekarang + tambahan_sks
        total_bobot = (ipk_sekarang * sks_sekarang) + tambahan_bobot

        prediksi_ipk = round(total_bobot / total_sks, 2) if total_sks > 0 else 0.0

        return {
            "ipk_sekarang": ipk_sekarang,
            "sks_sekarang": sks_sekarang,
            "tambahan_sks": tambahan_sks,
            "tambahan_bobot": round(tambahan_bobot, 2),
            "total_sks": total_sks,
            "prediksi_ipk": prediksi_ipk,
        }

    # ── Grafik Perkembangan ───────────────────────────────

    async def grafik_perkembangan(self, user_id: int) -> str:
        """Buat grafik perkembangan IPS per semester (ASCII bar chart)."""
        semesters = await self.repo.get_semesters(user_id)
        if not semesters:
            raise NotFoundError("Belum ada data nilai.")

        lines = ["<b>📈 Grafik Perkembangan IPS</b>\n"]
        max_bar = 20  # panjang maksimum bar

        for sem in semesters:
            ips_data = await self.hitung_ips(user_id, sem)
            ips = ips_data["ips"]
            bar_len = int((ips / 4.0) * max_bar)
            bar = "█" * bar_len + "░" * (max_bar - bar_len)
            lines.append(
                f"Semester {sem:>2}  {bar}  <b>{ips:.2f}</b>"
            )

        ipk_data = await self.hitung_ipk(user_id)
        lines.append(f"\n🎯 <b>IPK: {ipk_data['ipk']:.2f}</b>")

        return "\n".join(lines)

    # ── Riwayat Semester ──────────────────────────────────

    async def riwayat_semester(self, user_id: int) -> str:
        """Tampilkan riwayat lengkap per semester."""
        semesters = await self.repo.get_semesters(user_id)
        if not semesters:
            raise NotFoundError("Belum ada data nilai.")

        ipk_data = await self.hitung_ipk(user_id)
        lines = ["<b>📚 Riwayat Semester</b>\n"]

        for sem in semesters:
            ips_data = await self.hitung_ips(user_id, sem)
            nilai_list = await self.repo.list_by_user(user_id, sem)
            lines.append(
                f"━ <b>Semester {sem}</b> ━ IPS: {ips_data['ips']:.2f} "
                f"({ips_data['total_sks']} SKS)"
            )
            for n in nilai_list:
                lines.append(
                    f"  • {n.mata_kuliah} ({n.sks} SKS): "
                    f"{n.nilai:.2f} ({n.nilai_huruf})"
                )
            lines.append("")

        lines.append(f"🎯 <b>IPK Kumulatif: {ipk_data['ipk']:.2f}</b>")
        return "\n".join(lines)
