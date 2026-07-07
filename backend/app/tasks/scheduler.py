import logging

from apscheduler.schedulers.background import BackgroundScheduler

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
