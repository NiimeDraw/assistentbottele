"""Pembersihan file PDF sementara ringkasan."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.pdf_summary_service import PdfSummaryService
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def cleanup_pdf_summary_files() -> None:
    try:
        await PdfSummaryService.cleanup_expired_files()
    except Exception:  # noqa: BLE001
        logger.exception("Gagal membersihkan file PDF ringkasan yang kedaluwarsa")


def register_pdf_summary_cleanup(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        cleanup_pdf_summary_files,
        trigger="interval",
        hours=1,
        id="pdf_summary_cleanup_job",
        replace_existing=True,
    )
