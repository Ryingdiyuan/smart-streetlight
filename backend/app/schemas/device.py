from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    device_code: str
    device_name: str
    location: str | None = None


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
