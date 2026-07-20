"""
Scheduler pengingat untuk jadwal kuliah menggunakan APScheduler.
Memeriksa jadwal yang dimiliki user untuk hari ini, dan mengirim pengingat
pada waktu (jam_mulai - reminder_minutes) apabila waktu tersebut dekat.
"""
from datetime import datetime, date, time as dt_time, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from app.config.settings import settings
from app.database.session import get_session
from app.repositories.user_repository import UserRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory sent cache to avoid duplicate sends within the same day/session
_sent_cache: set[tuple[int, date, int]] = set()


async def check_and_send_schedule_reminders(bot: Bot) -> None:
    now = datetime.now()
    today_name = now.strftime("%A")
    # map English weekday to Bahasa values used in HariEnum
    mapping = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }
    hari_value = mapping.get(today_name)
    if not hari_value:
        return

    upper_bound = now + timedelta(minutes=30)

    async with get_session() as session:
        # cast session to AsyncSession for type checkers
        session = cast(AsyncSession, session)
        sched_repo = ScheduleRepository(session)
        
        # Use select-based query instead
        from sqlalchemy import select
        from app.models.schedule import HariEnum as _HariEnum
        result = await session.execute(
            select(sched_repo.model).where(sched_repo.model.hari == _HariEnum(hari_value))
        )
        schedules_today = list(result.scalars().all())

        logger.info("Menemukan %d jadwal untuk hari ini", len(schedules_today))

        for s in schedules_today:
            if not s.reminder_minutes:
                continue
            # construct today's datetime for jam_mulai
            start_dt = datetime.combine(now.date(), s.jam_mulai)
            reminder_dt = start_dt - timedelta(minutes=s.reminder_minutes)
            if reminder_dt < now or reminder_dt > upper_bound:
                continue
            cache_key = (s.id, now.date(), s.reminder_minutes)
            if cache_key in _sent_cache:
                continue
            telegram_id = getattr(s.user, "telegram_id", None)
            if telegram_id is None:
                continue
            # send reminder
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"⏰ <b>Pengingat Kuliah</b>\n\n"
                        f"{s.mata_kuliah}\n"
                        f"Hari: {s.hari.value if hasattr(s.hari, 'value') else s.hari}\n"
                        f"Jam: {s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}\n"
                        f"Ruangan: {s.ruangan or '-'}\n"
                        f"Dosen: {s.dosen or '-'}\n\n"
                        f"Pengingat {s.reminder_minutes} menit sebelum kelas."
                    ),
                )
                _sent_cache.add(cache_key)
            except Exception:
                logger.exception("Gagal mengirim pengingat jadwal untuk schedule_id=%s", s.id)


def register_schedule_reminder(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    # job interval based on REMINDER_CHECK_INTERVAL_MINUTES
    scheduler.add_job(
        check_and_send_schedule_reminders,
        trigger="interval",
        minutes=settings.REMINDER_CHECK_INTERVAL_MINUTES,
        args=[bot],
        id="schedule_reminder_job",
        replace_existing=True,
    )
