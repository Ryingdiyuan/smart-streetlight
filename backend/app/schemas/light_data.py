from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LightDataCreate(BaseModel):
    light_intensity: int
    lamp_status: str
    voltage: float | None = None
    reported_at: datetime | None = None


class LightDataRead(BaseModel):
    id: int
    device_id: int
    light_intensity: int
    lamp_status: str
    voltage: float | None = None
    reported_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LightDataWithAction(LightDataRead):
    suggested_action: str
