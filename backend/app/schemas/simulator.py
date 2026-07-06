from pydantic import BaseModel


class SimulatorConfigUpdate(BaseModel):
    enabled: bool
    host: str
    port: int
    username: str = ""
    password: str = ""


class SimulatorConfigRead(SimulatorConfigUpdate):
    client_id: str
    connected: bool


class SimulatorDeviceCreate(BaseModel):
    device_code: str
    device_name: str
    location: str | None = None
    status: str = "offline"
    base_light: int = 120
    variance: int = 35
    voltage_base: float = 220.5
    telemetry_interval_seconds: int = 5
    status_every: int = 1
    online: bool = True
    auto_start: bool = True


class SimulatorDeviceUpdate(BaseModel):
    device_name: str | None = None
    location: str | None = None
    status: str | None = None
    base_light: int | None = None
    variance: int | None = None
    voltage_base: float | None = None
    telemetry_interval_seconds: int | None = None
    status_every: int | None = None
    online: bool | None = None
    running: bool | None = None


class SimulatorDeviceRead(BaseModel):
    device_id: int
    device_code: str
    device_name: str
    location: str | None = None
    running: bool
    online: bool
    system_status: str
    lamp_status: str
    brightness: int
    base_light: int
    variance: int
    voltage_base: float
    telemetry_interval_seconds: int
    status_every: int
    publish_count: int
    current_light_intensity: int
    last_telemetry_at: str | None = None
    last_status_at: str | None = None
    last_command_at: str | None = None
    last_command: str | None = None


class SimulatorLogRead(BaseModel):
    created_at: str
    level: str
    message: str
