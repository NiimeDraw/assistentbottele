"""
Scheduler pengingat untuk jadwal kuliah menggunakan APScheduler.
Memeriksa jadwal yang dimiliki user untuk hari ini, dan mengirim pengingat
pada waktu (jam_mulai - reminder_minutes) apabila waktu tersebut dekat.
"""
from datetime import datetime, date, time as dt_time, timedelta

# pyrefly: ignore [missing-import]
from aiogram import Bot
# pyrefly: ignore [missing-import]
from app.utils.html import quote
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from typing import cast

# pyrefly: ignore [missing-import]
from app.config.settings import settings
# pyrefly: ignore [missing-import]
from app.database.session import get_session
# pyrefly: ignore [missing-import]
from app.models.schedule import hari_from_date
# pyrefly: ignore [missing-import]
from app.repositories.schedule_repository import ScheduleRepository
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger
# pyrefly: ignore [missing-import]
from app.utils.timezone_utils import APP_TZ, now_local

logger = get_logger(__name__)

# In-memory sent cache to avoid duplicate sends within the same day/session
_sent_cache: set[tuple[int, date, int]] = set()


async def check_and_send_schedule_reminders(bot: Bot) -> None:
    now = now_local()
    today = now.date()

    # Bersihkan cache dari hari-hari sebelumnya agar memori tidak bocor
    _sent_cache.difference_update({k for k in _sent_cache if k[1] < today})

    hari_enum = hari_from_date(today)

    async with get_session() as session:
        session = cast(AsyncSession, session)
        sched_repo = ScheduleRepository(session)

        # pyrefly: ignore [missing-import]
        from sqlalchemy import select
        # pyrefly: ignore [missing-import]
        from sqlalchemy.orm import selectinload

        # Eager load s.user untuk menghindari MissingGreenlet error di async SQLAlchemy
        result = await session.execute(
            select(sched_repo.model)
            .options(selectinload(sched_repo.model.user))
            .where(sched_repo.model.hari == hari_enum)
        )
        schedules_today = list(result.scalars().all())

        logger.info("Menemukan %d jadwal untuk hari ini", len(schedules_today))

        for s in schedules_today:
            if not s.reminder_minutes:
                continue

            # Gunakan timezone yang sama (APP_TZ / WIB)
            start_dt = datetime.combine(today, s.jam_mulai, tzinfo=APP_TZ)
            reminder_dt = start_dt - timedelta(minutes=s.reminder_minutes)

            # Jika waktu pengingat belum tiba, lewati
            if reminder_dt > now:
                continue

            # Jika waktu pengingat sudah lewat lebih dari interval toleransi (15 menit), jangan spam
            if (now - reminder_dt) > timedelta(minutes=15):
                continue

            cache_key = (s.id, today, s.reminder_minutes)
            if cache_key in _sent_cache:
                continue

            user = s.user
            if not user or not user.telegram_id:
                continue

            try:
                ruangan_str = quote(s.ruangan) if s.ruangan else "-"
                dosen_str = quote(s.dosen) if s.dosen else "-"
                matkul_str = quote(s.mata_kuliah)
                hari_str = s.hari.value if hasattr(s.hari, "value") else str(s.hari)

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=(
                        f"⏰ <b>Pengingat Kuliah</b>\n\n"
                        f"{matkul_str}\n"
                        f"Hari: {hari_str}\n"
                        f"Jam: {s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}\n"
                        f"Ruangan: {ruangan_str}\n"
                        f"Dosen: {dosen_str}\n\n"
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
