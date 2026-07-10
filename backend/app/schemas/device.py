from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    device_code: str
    device_name: str
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "offline"
    sensor_id: int | None = None
    lamp_status: str = "OFF"
    control_mode: str = "manual"


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_code: str | None = None
    device_name: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str | None = None
    sensor_id: int | None = None
    lamp_status: str | None = None
    control_mode: str | None = None


class DeviceRead(DeviceBase):
    id: int
    last_heartbeat_at: datetime | None = None
    sensor_code: str | None = None
    sensor_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
