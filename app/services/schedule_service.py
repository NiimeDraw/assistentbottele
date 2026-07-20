"""Service layer untuk fitur Jadwal Kuliah (Schedule)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import HariEnum, Schedule
from app.repositories.schedule_repository import ScheduleRepository
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.validators import validate_non_empty, validate_time


class ScheduleService:
    def __init__(self, session: AsyncSession):
        self.repo = ScheduleRepository(session)

    async def create_schedule(
        self,
        user_id: int,
        mata_kuliah: str,
        hari: str,
        jam_mulai_raw: str,
        jam_selesai_raw: str,
        ruangan: str | None = None,
        dosen: str | None = None,
        reminder_minutes: int | None = None,
    ) -> Schedule:
        mata_kuliah = validate_non_empty(mata_kuliah, "Nama mata kuliah")
        try:
            hari_enum = HariEnum(hari)
        except ValueError:
            raise ValidationError("Hari tidak valid. Pilih salah satu hari Senin-Minggu.")

        jam_mulai = validate_time(jam_mulai_raw, "Jam mulai")
        jam_selesai = validate_time(jam_selesai_raw, "Jam selesai")
        if jam_selesai <= jam_mulai:
            raise ValidationError("Jam selesai harus lebih besar dari jam mulai.")

        schedule = Schedule(
            user_id=user_id,
            mata_kuliah=mata_kuliah,
            hari=hari_enum,
            jam_mulai=jam_mulai,
            jam_selesai=jam_selesai,
            ruangan=(ruangan or "").strip() or None,
            dosen=(dosen or "").strip() or None,
            reminder_minutes=reminder_minutes,
        )
        return await self.repo.add(schedule)

    async def list_schedules(self, user_id: int) -> list[Schedule]:
        return await self.repo.list_by_user(user_id)

    async def get_schedule(self, schedule_id: int, user_id: int) -> Schedule:
        schedule = await self.repo.get_by_id_for_user(schedule_id, user_id)
        if not schedule:
            raise NotFoundError("Jadwal tidak ditemukan atau bukan milik Anda.")
        return schedule

    async def delete_schedule(self, schedule_id: int, user_id: int) -> None:
        schedule = await self.get_schedule(schedule_id, user_id)
        await self.repo.delete(schedule)

    async def update_schedule(self, schedule_id: int, user_id: int, **kwargs) -> Schedule:
        schedule = await self.get_schedule(schedule_id, user_id)
        allowed = {"mata_kuliah", "hari", "jam_mulai", "jam_selesai", "ruangan", "dosen", "reminder_minutes"}
        updated = False

        # handle conversions
        if "hari" in kwargs and kwargs["hari"] is not None:
            try:
                kwargs["hari"] = HariEnum(kwargs["hari"]) if not isinstance(kwargs["hari"], HariEnum) else kwargs["hari"]
            except Exception:
                raise ValidationError("Hari tidak valid untuk update.")

        if "jam_mulai" in kwargs and kwargs["jam_mulai"]:
            kwargs["jam_mulai"] = validate_time(kwargs["jam_mulai"], "Jam mulai")
        if "jam_selesai" in kwargs and kwargs["jam_selesai"]:
            kwargs["jam_selesai"] = validate_time(kwargs["jam_selesai"], "Jam selesai")

        for k, v in kwargs.items():
            if k in allowed and getattr(schedule, k) != v:
                setattr(schedule, k, v)
                updated = True
        if updated:
            await self.repo.session.flush()
        return schedule
