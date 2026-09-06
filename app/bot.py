"""
Bootstrap Bot & Dispatcher: registrasi middleware dan router (handler).
Dipisah dari main.py agar mudah diuji dan digunakan ulang (mis. untuk webhook).
"""
from app.config.settings import settings
from app.handlers import (
    academic_handlers,
    ai_handlers,
    common,
    dashboard_handlers,
    nilai_handlers,
    note_handlers,
    profile_handlers,
    schedule_handlers,
    task_handlers,
)
from app.middlewares.db_middleware import DbSessionMiddleware
from app.middlewares.error_middleware import ErrorHandlerMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.menu_middleware import MenuNavigationMiddleware
from app.middlewares.user_middleware import UserMiddleware


def create_bot():
    # Import aiogram lazily to avoid heavy import time at module import stage
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher():
    # Import here to avoid importing aiogram at module import time
    from aiogram import Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage

    dp = Dispatcher(storage=MemoryStorage())

    # Urutan middleware penting: error handler (terluar) -> logging -> db session -> resolve user
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())

    # Middleware pencegahan tabrakan FSM dengan tombol menu navigasi
    dp.message.outer_middleware(MenuNavigationMiddleware())

    # Registrasi router per fitur (modular per handler)
    dp.include_router(common.router)
    dp.include_router(academic_handlers.router)
    dp.include_router(dashboard_handlers.router)
    dp.include_router(task_handlers.router)
    dp.include_router(schedule_handlers.router)
    dp.include_router(note_handlers.router)
    dp.include_router(ai_handlers.router)
    dp.include_router(profile_handlers.router)
    dp.include_router(nilai_handlers.router)

    return dp