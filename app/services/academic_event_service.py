"""Service layer untuk fitur Kalender Akademik (AcademicEvent)."""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_event import AcademicEvent, EventTypeEnum
from app.repositories.academic_event_repository import AcademicEventRepository
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.validators import validate_date, validate_non_empty, validate_optional_int


class AcademicEventService:
    def __init__(self, session: AsyncSession):
        self.repo = AcademicEventRepository(session)

    async def create_event(
        self,
        user_id: int,
        title: str,
        event_type_raw: str,
        start_date_raw: str,
        end_date_raw: str | None = None,
        location: str | None = None,
        description: str | None = None,
        reminder_days_before_raw: str | None = None,
    ) -> AcademicEvent:
        title = validate_non_empty(title, "Judul event")

        try:
            event_type = EventTypeEnum(event_type_raw)
        except ValueError:
            raise ValidationError("Jenis event tidak valid.")

        start_date = validate_date(start_date_raw, "Tanggal mulai")

        end_date: date | None = None
        if end_date_raw and end_date_raw.strip() != "-":
            end_date = validate_date(end_date_raw, "Tanggal selesai")
            if end_date < start_date:
                raise ValidationError("Tanggal selesai tidak boleh sebelum tanggal mulai.")

        reminder_days_before = None
        if reminder_days_before_raw is not None:
            reminder_days_before = validate_optional_int(
                reminder_days_before_raw, "Pengingat (hari sebelum)", min_value=0
            )

        event = AcademicEvent(
            user_id=user_id,
            title=title,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            location=(location or "").strip() or None,
            description=(description or "").strip() or None,
            reminder_days_before=reminder_days_before,
        )
        return await self.repo.add(event)

    async def list_events(self, user_id: int) -> list[AcademicEvent]:
        return await self.repo.list_by_user(user_id)

    async def list_events_by_month(self, user_id: int, year: int, month: int) -> list[AcademicEvent]:
        return await self.repo.list_by_month(user_id, year, month)

    async def search_events(self, user_id: int, keyword: str) -> list[AcademicEvent]:
        keyword = validate_non_empty(keyword, "Kata kunci pencarian", max_length=100)
        return await self.repo.search(user_id, keyword)

    async def get_event(self, event_id: int, user_id: int) -> AcademicEvent:
        event = await self.repo.get_by_id_for_user(event_id, user_id)
        if not event:
            raise NotFoundError("Event tidak ditemukan atau bukan milik Anda.")
        return event

    async def delete_event(self, event_id: int, user_id: int) -> None:
        event = await self.get_event(event_id, user_id)
        await self.repo.delete(event)

    async def list_events_due_for_reminder(self, today: date) -> list[AcademicEvent]:
        """
        Ambil event yang sudah waktunya diingatkan hari ini, yaitu:
        reminder_days_before terisi, belum terkirim, dan
        (start_date - reminder_days_before) <= today <= start_date.
        """
        candidates = await self.repo.list_pending_reminders(today)
        due: list[AcademicEvent] = []
        for event in candidates:
            if event.reminder_days_before is None:
                continue
            days_until_start = (event.start_date - today).days
            if days_until_start <= event.reminder_days_before:
                due.append(event)
        return due