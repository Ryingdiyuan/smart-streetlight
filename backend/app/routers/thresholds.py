from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.threshold_config import ThresholdConfig
from app.schemas.threshold_config import ThresholdConfigRead, ThresholdConfigUpdate
from app.services.auto_control import (
    get_or_create_threshold_config,
    validate_threshold_range,
)

router = APIRouter(prefix="/devices/{device_id}/threshold", tags=["thresholds"])


def ensure_device_exists(db: Session, device_id: int) -> None:
    if db.get(Device, device_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在",
        )


@router.get("", response_model=ThresholdConfigRead)
def get_threshold_config(
    device_id: int,
    db: Session = Depends(get_db),
) -> ThresholdConfig:
    ensure_device_exists(db, device_id)
    return get_or_create_threshold_config(db, device_id)


@router.put("", response_model=ThresholdConfigRead)
def update_threshold_config(
    device_id: int,
    threshold_update: ThresholdConfigUpdate,
    db: Session = Depends(get_db),
) -> ThresholdConfig:
    ensure_device_exists(db, device_id)

    try:
        validate_threshold_range(
            threshold_update.low_threshold,
            threshold_update.high_threshold,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="low_threshold 必须小于 high_threshold",
        ) from None

    config = get_or_create_threshold_config(db, device_id)
    config.low_threshold = threshold_update.low_threshold
    config.high_threshold = threshold_update.high_threshold
    config.enabled = threshold_update.enabled

    db.commit()
    db.refresh(config)
    return config
