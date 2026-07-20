"""
Scheduler pengingat event Kalender Akademik menggunakan APScheduler.
Berjalan sekali sehari, memeriksa event yang sudah waktunya diingatkan
(sesuai reminder_days_before masing-masing), lalu mengirim notifikasi.
"""
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.session import get_session
from app.models.academic_event import EVENT_TYPE_EMOJI
from app.repositories.user_repository import UserRepository
from app.services.academic_event_service import AcademicEventService
from app.utils.logger import get_logger
from app.utils.timezone_utils import now_local

logger = get_logger(__name__)


async def check_and_send_academic_reminders(bot: Bot) -> None:
    """Job yang dipanggil APScheduler sekali sehari."""
    today = now_local().date()

    async with get_session() as session:
        event_service = AcademicEventService(session)
        user_repo = UserRepository(session)

        due_events = await event_service.list_events_due_for_reminder(today)
        logger.info("Ditemukan %d event akademik yang perlu diingatkan", len(due_events))

        for event in due_events:
            user = await user_repo.get_by_id(event.user_id)
            if not user:
                continue
            try:
                emoji = EVENT_TYPE_EMOJI.get(event.event_type, "")
                selisih_hari = (event.start_date - today).days
                kapan = "hari ini" if selisih_hari == 0 else f"{selisih_hari} hari lagi"
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=(
                        f"📅 <b>Pengingat Kalender Akademik!</b>\n\n"
                        f"{emoji} <b>{event.event_type.value}</b>: {event.title}\n"
                        f"Tanggal: {event.start_date.strftime('%d-%m-%Y')} ({kapan})\n"
                        f"{'Lokasi: ' + event.location if event.location else ''}"
                    ),
                )
                event.reminder_sent = True
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Gagal mengirim reminder akademik ke user_id=%s", user.telegram_id
                )


def setup_academic_reminder_job(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    """
    Daftarkan job ke scheduler yang sudah ada (dipanggil dari main.py).
    Dijalankan sekali sehari jam 07:00 WIB — waktu yang wajar untuk
    pengingat harian tanpa mengganggu pengguna di jam tidur.
    """
    scheduler.add_job(
        check_and_send_academic_reminders,
        trigger="cron",
        hour=7,
        minute=0,
        args=[bot],
        id="academic_reminder_job",
        replace_existing=True,
    )