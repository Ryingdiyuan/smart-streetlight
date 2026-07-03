from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ThresholdConfigUpdate(BaseModel):
    low_threshold: int
    high_threshold: int
    enabled: bool = True


class ThresholdConfigRead(BaseModel):
    id: int
    device_id: int
    low_threshold: int
    high_threshold: int
    enabled: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
