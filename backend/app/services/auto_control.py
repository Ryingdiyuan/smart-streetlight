import logging

from sqlalchemy.orm import Session

from app.models.threshold_config import ThresholdConfig

logger = logging.getLogger(__name__)

DEFAULT_LOW_THRESHOLD = 100
DEFAULT_HIGH_THRESHOLD = 300
DEFAULT_ENABLED = True

ACTION_TURN_ON = "TURN_ON"
ACTION_TURN_OFF = "TURN_OFF"
ACTION_KEEP = "KEEP"
ACTION_DISABLED = "DISABLED"


def validate_threshold_range(low_threshold: int, high_threshold: int) -> None:
    if low_threshold >= high_threshold:
        raise ValueError("low_threshold must be less than high_threshold")


def get_or_create_threshold_config(db: Session, device_id: int) -> ThresholdConfig:
    config = (
        db.query(ThresholdConfig)
        .filter(ThresholdConfig.device_id == device_id)
        .first()
    )
    if config is not None:
        return config

    config = ThresholdConfig(
        device_id=device_id,
        low_threshold=DEFAULT_LOW_THRESHOLD,
        high_threshold=DEFAULT_HIGH_THRESHOLD,
        enabled=DEFAULT_ENABLED,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def evaluate_auto_control(
    db: Session,
    device_id: int,
    light_intensity: int,
) -> str:
    config = get_or_create_threshold_config(db, device_id)

    if not config.enabled:
        action = ACTION_DISABLED
    elif light_intensity < config.low_threshold:
        action = ACTION_TURN_ON
    elif light_intensity > config.high_threshold:
        action = ACTION_TURN_OFF
    else:
        action = ACTION_KEEP

    logger.info(
        "Auto control result device_id=%s light_intensity=%s action=%s",
        device_id,
        light_intensity,
        action,
    )
    return action
