"""
Scheduler pengingat deadline tugas menggunakan APScheduler.
Berjalan berkala, memeriksa tugas yang deadline-nya sudah dekat,
lalu mengirim notifikasi Telegram ke pengguna terkait.
"""
from datetime import timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.settings import settings
from app.database.session import get_session
from app.repositories.user_repository import UserRepository
from app.services.task_service import TaskService
from app.utils.logger import get_logger
from app.utils.timezone_utils import format_local, now_local

logger = get_logger(__name__)


async def check_and_send_reminders(bot: Bot) -> None:
    """Job yang dipanggil APScheduler secara berkala."""
    # Pakai now_local() (WIB, timezone-aware) bukan datetime.now() (naive),
    # supaya konsisten dengan kolom deadline yang tz-aware di database,
    # terlepas dari timezone server tempat bot dijalankan.
    upper_bound = now_local() + timedelta(minutes=settings.REMINDER_BEFORE_MINUTES)

    async with get_session() as session:
        task_service = TaskService(session)
        user_repo = UserRepository(session)

        due_tasks = await task_service.list_due_for_reminder(upper_bound)
        logger.info("Ditemukan %d tugas yang perlu diingatkan", len(due_tasks))

        for task in due_tasks:
            user = await user_repo.get_by_id(task.user_id)
            if not user:
                continue
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=(
                        f"⏰ <b>Pengingat Tugas!</b>\n\n"
                        f"📌 {task.title}\n"
                        f"Deadline: {format_local(task.deadline)}\n\n"
                        f"Jangan lupa dikerjakan ya!"
                    ),
                )
                task.reminder_sent = True
            except Exception:  # noqa: BLE001
                logger.exception("Gagal mengirim reminder ke user_id=%s", user.telegram_id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        minutes=settings.REMINDER_CHECK_INTERVAL_MINUTES,
        args=[bot],
        id="task_reminder_job",
        replace_existing=True,
    )
    return scheduler