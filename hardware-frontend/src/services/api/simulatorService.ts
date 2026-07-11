import { http } from "@/lib/http";
import type {
  SimulatorBatchControlSummary,
  SimulatorBrokerConfig,
  SimulatorLogEntry,
  SimulatorSensor,
} from "@/types/models";

interface SimulatorBrokerConfigPayload {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password: string;
  client_id: string;
  connected: boolean;
}

interface SimulatorSensorPayload {
  sensor_id: number;
  sensor_code: string;
  sensor_name: string;
  location: string | null;
  running: boolean;
  online: boolean;
  system_status: "online" | "offline";
  lamp_status: "on" | "off";
  brightness: number;
  base_light: number;
  variance: number;
  voltage_base: number;
  telemetry_interval_seconds: number;
  status_every: number;
  publish_count: number;
  current_light_intensity: number;
  last_telemetry_at?: string | null;
  last_status_at?: string | null;
  last_command_at?: string | null;
  last_command?: string | null;
  bound_device_id?: number | null;
  bound_device_code?: string | null;
  bound_device_name?: string | null;
  control_mode?: "manual" | "auto" | null;
}

interface SimulatorLogPayload {
  created_at: string;
  level: string;
  message: string;
}

interface SimulatorBatchControlItemPayload {
  sensor_id: number;
  sensor_code: string;
  result: "success" | "failed";
  running: boolean;
}

interface SimulatorBatchControlPayload {
  action: "start" | "stop";
  total: number;
  success_count: number;
  failed_count: number;
  results: SimulatorBatchControlItemPayload[];
}

export interface SimulatorConfigInput {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password: string;
}

export interface SimulatorSensorInput {
  sensorCode: string;
  sensorName: string;
  location: string;
  baseLight: number;
  variance: number;
  voltageBase: number;
  telemetryIntervalSeconds: number;
  statusEvery: number;
  online: boolean;
  autoStart: boolean;
}

export interface SimulatorSensorUpdateInput {
  sensorName: string;
  location: string;
  baseLight: number;
  variance: number;
  voltageBase: number;
  telemetryIntervalSeconds: number;
  statusEvery: number;
  online: boolean;
  running: boolean;
}

function normalizeText(value?: string | null) {
  return value ?? "";
}

function mapConfig(payload: SimulatorBrokerConfigPayload): SimulatorBrokerConfig {
  return {
    enabled: payload.enabled,
    host: payload.host,
    port: payload.port,
    username: payload.username,
    password: payload.password,
    clientId: payload.client_id,
    connected: payload.connected,
  };
}

function mapSensor(payload: SimulatorSensorPayload): SimulatorSensor {
  return {
    sensorId: payload.sensor_id,
    sensorCode: payload.sensor_code,
    sensorName: payload.sensor_name,
    location: normalizeText(payload.location),
    running: payload.running,
    online: payload.online,
    systemStatus: payload.system_status === "online" ? "online" : "offline",
    lampStatus: payload.lamp_status,
    brightness: payload.brightness,
    baseLight: payload.base_light,
    variance: payload.variance,
    voltageBase: payload.voltage_base,
    telemetryIntervalSeconds: payload.telemetry_interval_seconds,
    statusEvery: payload.status_every,
    publishCount: payload.publish_count,
    currentLightIntensity: payload.current_light_intensity,
    lastTelemetryAt: normalizeText(payload.last_telemetry_at),
    lastStatusAt: normalizeText(payload.last_status_at),
    lastCommandAt: normalizeText(payload.last_command_at),
    lastCommand: normalizeText(payload.last_command),
    boundDeviceId: payload.bound_device_id ?? undefined,
    boundDeviceCode: payload.bound_device_code ?? undefined,
    boundDeviceName: payload.bound_device_name ?? undefined,
    controlMode: payload.control_mode ?? undefined,
  };
}

function mapLog(payload: SimulatorLogPayload): SimulatorLogEntry {
  return {
    createdAt: payload.created_at,
    level: payload.level,
    message: payload.message,
  };
}

function mapBatchControlSummary(payload: SimulatorBatchControlPayload): SimulatorBatchControlSummary {
  return {
    action: payload.action,
    total: payload.total,
    successCount: payload.success_count,
    failedCount: payload.failed_count,
    results: payload.results.map((item) => ({
      sensorId: item.sensor_id,
      sensorCode: item.sensor_code,
      result: item.result,
      running: item.running,
    })),
  };
}

export async function getSimulatorConfig(): Promise<SimulatorBrokerConfig> {
  const payload = await http.get<SimulatorBrokerConfigPayload>("/simulator/config");
  return mapConfig(payload);
}

export async function updateSimulatorConfig(config: SimulatorConfigInput): Promise<SimulatorBrokerConfig> {
  const payload = await http.put<SimulatorBrokerConfigPayload>("/simulator/config", config);
  return mapConfig(payload);
}

export async function getSimulatorSensors(): Promise<SimulatorSensor[]> {
  const payload = await http.get<SimulatorSensorPayload[]>("/simulator/sensors");
  return payload.map(mapSensor);
}

export async function registerSimulatorSensor(input: SimulatorSensorInput): Promise<SimulatorSensor> {
  const payload = await http.post<SimulatorSensorPayload>("/simulator/sensors/register", {
    sensor_code: input.sensorCode,
    sensor_name: input.sensorName,
    location: input.location || null,
    status: "offline",
    base_light: input.baseLight,
    variance: input.variance,
    voltage_base: input.voltageBase,
    telemetry_interval_seconds: input.telemetryIntervalSeconds,
    status_every: input.statusEvery,
    online: input.online,
    auto_start: input.autoStart,
  });
  return mapSensor(payload);
}

export async function startSimulatorSensor(sensorId: number): Promise<SimulatorSensor> {
  const payload = await http.post<SimulatorSensorPayload>(`/simulator/sensors/${sensorId}/start`);
  return mapSensor(payload);
}

export async function stopSimulatorSensor(sensorId: number): Promise<SimulatorSensor> {
  const payload = await http.post<SimulatorSensorPayload>(`/simulator/sensors/${sensorId}/stop`);
  return mapSensor(payload);
}

export async function deleteSimulatorSensor(sensorId: number): Promise<void> {
  await http.delete(`/simulator/sensors/${sensorId}`);
}

export async function updateSimulatorSensor(
  sensorId: number,
  input: SimulatorSensorUpdateInput,
): Promise<SimulatorSensor> {
  const payload = await http.put<SimulatorSensorPayload>(`/simulator/sensors/${sensorId}`, {
    sensor_name: input.sensorName,
    location: input.location || null,
    base_light: input.baseLight,
    variance: input.variance,
    voltage_base: input.voltageBase,
    telemetry_interval_seconds: input.telemetryIntervalSeconds,
    status_every: input.statusEvery,
    online: input.online,
    running: input.running,
  });
  return mapSensor(payload);
}

export async function updateSimulatorSensorsRunning(
  sensorIds: number[],
  running: boolean,
): Promise<SimulatorBatchControlSummary> {
  const payload = await http.put<SimulatorBatchControlPayload>("/simulator/sensors/running/batch", {
    sensor_ids: sensorIds,
    running,
  });
  return mapBatchControlSummary(payload);
}

export async function getSimulatorLogs(limit = 120, level?: string): Promise<SimulatorLogEntry[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    ...(level ? { level } : {}),
  });
  const payload = await http.get<SimulatorLogPayload[]>(`/simulator/logs?${query.toString()}`);
  return payload.map(mapLog);
}

export async function clearSimulatorLogs(): Promise<void> {
  await http.delete("/simulator/logs");
}
