"""
Entry point aplikasi Campus Assistant Bot.
Menjalankan polling Telegram bot beserta scheduler pengingat tugas.
"""
import asyncio
import sys

# Fix untuk Windows: psycopg (async) tidak kompatibel dengan ProactorEventLoop
# yang menjadi default di Windows. Harus dipaksa pakai SelectorEventLoop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# pyrefly: ignore [missing-import]
from app.bot import create_bot, create_dispatcher
# pyrefly: ignore [missing-import]
from app.scheduler.academic_reminder_scheduler import setup_academic_reminder_job
# pyrefly: ignore [missing-import]
from app.scheduler.reminder_scheduler import setup_scheduler
# pyrefly: ignore [missing-import]
from app.scheduler.schedule_reminder import register_schedule_reminder
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger, setup_logging
from app.config.settings import validate_required_settings

logger = get_logger(__name__)


async def main() -> None:
    setup_logging()
    validate_required_settings()
    logger.info("Menjalankan Campus Assistant Bot...")

    bot = create_bot()
    dp = create_dispatcher()

    scheduler = setup_scheduler(bot)
    # register schedule reminders & academic reminders onto the same scheduler
    register_schedule_reminder(scheduler, bot)
    setup_academic_reminder_job(scheduler, bot)
    scheduler.start()
    logger.info("Scheduler pengingat aktif (tugas, jadwal kuliah & kalender akademik).")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot dihentikan.")