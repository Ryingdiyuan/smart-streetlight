import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.services.offline_check import run_offline_check

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def check_device_offline() -> None:
    run_offline_check()


scheduler.add_job(
    check_device_offline,
    "interval",
    seconds=60,
    id="check_device_offline",
    replace_existing=True,
)

# Cloud-to-local incremental sync (only when cloud DB is enabled)
if settings.cloud_db_enabled:
    from app.services.db_sync import incremental_sync_from_cloud

    scheduler.add_job(
        incremental_sync_from_cloud,
        "interval",
        seconds=settings.db_sync_interval_seconds,
        id="db_sync",
        replace_existing=True,
    )
    logger.info(
        "[scheduler] DB sync job registered every %s seconds",
        settings.db_sync_interval_seconds,
    )
