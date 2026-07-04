from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    device_code: str
    device_name: str
    location: str | None = None
    status: str = "offline"


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_code: str | None = None
    device_name: str | None = None
    location: str | None = None
    status: str | None = None


class DeviceRead(DeviceBase):
    id: int
    last_heartbeat_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
