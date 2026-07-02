from fastapi import APIRouter, HTTPException, status

from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["devices"])

devices: dict[int, DeviceRead] = {}
next_device_id = 1


def get_device_or_404(device_id: int) -> DeviceRead:
    device = devices.get(device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在",
        )
    return device


def ensure_device_code_unique(device_code: str, exclude_id: int | None = None) -> None:
    for device_id, device in devices.items():
        if device_id != exclude_id and device.device_code == device_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设备编码已存在",
            )


@router.get("", response_model=list[DeviceRead])
def list_devices() -> list[DeviceRead]:
    return list(devices.values())


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: int) -> DeviceRead:
    return get_device_or_404(device_id)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(device_create: DeviceCreate) -> DeviceRead:
    global next_device_id

    ensure_device_code_unique(device_create.device_code)

    device = DeviceRead(id=next_device_id, **device_create.model_dump())
    devices[next_device_id] = device
    next_device_id += 1
    return device


@router.put("/{device_id}", response_model=DeviceRead)
def update_device(device_id: int, device_update: DeviceUpdate) -> DeviceRead:
    old_device = get_device_or_404(device_id)
    update_data = device_update.model_dump(exclude_unset=True)

    if "device_code" in update_data:
        ensure_device_code_unique(update_data["device_code"], exclude_id=device_id)

    new_device = old_device.model_copy(update=update_data)
    devices[device_id] = new_device
    return new_device


@router.delete("/{device_id}")
def delete_device(device_id: int) -> dict[str, str]:
    get_device_or_404(device_id)
    del devices[device_id]
    return {"message": "删除成功"}
