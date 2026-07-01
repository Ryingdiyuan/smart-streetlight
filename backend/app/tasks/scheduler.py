import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def check_device_offline() -> None:
    logger.info("Device offline check placeholder")


scheduler.add_job(
    check_device_offline,
    "interval",
    seconds=60,
    id="check_device_offline",
    replace_existing=True,
)
