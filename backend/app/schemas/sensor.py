from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorBase(BaseModel):
    sensor_code: str
    sensor_name: str
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "offline"


class SensorCreate(SensorBase):
    online: bool = True
    base_light: int = 120
    variance: int = 35
    voltage_base: float = 220.5
    telemetry_interval_seconds: int = 20
    status_every: int = 1


class SensorUpdate(BaseModel):
    sensor_code: str | None = None
    sensor_name: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str | None = None
    online: bool | None = None
    base_light: int | None = None
    variance: int | None = None
    voltage_base: float | None = None
    telemetry_interval_seconds: int | None = None
    status_every: int | None = None


class SensorRead(SensorBase):
    id: int
    online: bool
    base_light: int
    variance: int
    voltage_base: float
    telemetry_interval_seconds: int
    status_every: int
    last_heartbeat_at: datetime | None = None
    bound_device_id: int | None = None
    bound_device_code: str | None = None
    bound_device_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
