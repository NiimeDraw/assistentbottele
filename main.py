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

from app.bot import create_bot, create_dispatcher
from app.scheduler.reminder_scheduler import setup_scheduler
from app.scheduler.schedule_reminder import register_schedule_reminder
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> None:
    setup_logging()
    logger.info("Menjalankan Campus Assistant Bot...")

    bot = create_bot()
    dp = create_dispatcher()

    scheduler = setup_scheduler(bot)
    # register schedule reminders onto the same scheduler
    register_schedule_reminder(scheduler, bot)
    scheduler.start()
    logger.info("Scheduler pengingat tugas aktif (tugas & jadwal).")

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