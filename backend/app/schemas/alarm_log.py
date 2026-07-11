from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlarmLogRead(BaseModel):
    id: int
    device_id: int | None = None
    sensor_id: int | None = None
    device_code: str | None = None
    sensor_code: str | None = None
    sensor_name: str | None = None
    alarm_type: str
    alarm_level: str
    alarm_content: str
    handled: bool
    handled_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
