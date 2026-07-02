from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["devices"])


def get_device_or_404(db: Session, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在",
        )
    return device


def ensure_device_code_unique(
    db: Session,
    device_code: str,
    exclude_id: int | None = None,
) -> None:
    query = db.query(Device).filter(Device.device_code == device_code)
    if exclude_id is not None:
        query = query.filter(Device.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设备编码已存在",
        )


@router.get("", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db)) -> list[Device]:
    return db.query(Device).order_by(Device.id.asc()).all()


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: int, db: Session = Depends(get_db)) -> Device:
    return get_device_or_404(db, device_id)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    device_create: DeviceCreate,
    db: Session = Depends(get_db),
) -> Device:
    ensure_device_code_unique(db, device_create.device_code)

    device = Device(**device_create.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
) -> Device:
    device = get_device_or_404(db, device_id)
    update_data = device_update.model_dump(exclude_unset=True)

    if "device_code" in update_data:
        ensure_device_code_unique(db, update_data["device_code"], exclude_id=device_id)

    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    device = get_device_or_404(db, device_id)
    db.delete(device)
    db.commit()
    return {"message": "删除成功"}
