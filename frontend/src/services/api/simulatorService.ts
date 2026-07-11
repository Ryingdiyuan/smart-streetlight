import { http } from "@/lib/http";
import type {
  SimulatorBrokerConfig,
  SimulatorDevice,
  SimulatorLogEntry,
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

interface SimulatorDevicePayload {
  device_id: number;
  device_code: string;
  device_name: string;
  location: string | null;
  running: boolean;
  online: boolean;
  system_status: "online" | "offline";
  lamp_status: "on" | "off";
  brightness: number;
  base_light: number;
  variance: number;
  voltage_base: number;
  telemetry_enabled: boolean;
  telemetry_interval_seconds: number;
  status_every: number;
  publish_count: number;
  current_light_intensity: number;
  last_telemetry_at?: string | null;
  last_status_at?: string | null;
  last_command_at?: string | null;
  last_command?: string | null;
}

interface SimulatorLogPayload {
  created_at: string;
  level: string;
  message: string;
}

export interface SimulatorConfigInput {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password: string;
}

export interface SimulatorDeviceInput {
  deviceCode: string;
  deviceName: string;
  location: string;
  baseLight: number;
  variance: number;
  voltageBase: number;
  telemetryEnabled: boolean;
  telemetryIntervalSeconds: number;
  statusEvery: number;
  online: boolean;
  autoStart: boolean;
}

export interface SimulatorDeviceUpdateInput {
  deviceName: string;
  location: string;
  baseLight: number;
  variance: number;
  voltageBase: number;
  telemetryEnabled: boolean;
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

function mapDevice(payload: SimulatorDevicePayload): SimulatorDevice {
  return {
    deviceId: payload.device_id,
    deviceCode: payload.device_code,
    deviceName: payload.device_name,
    location: normalizeText(payload.location),
    running: payload.running,
    online: payload.online,
    systemStatus: payload.system_status === "online" ? "online" : "offline",
    lampStatus: payload.lamp_status,
    brightness: payload.brightness,
    baseLight: payload.base_light,
    variance: payload.variance,
    voltageBase: payload.voltage_base,
    telemetryEnabled: payload.telemetry_enabled,
    telemetryIntervalSeconds: payload.telemetry_interval_seconds,
    statusEvery: payload.status_every,
    publishCount: payload.publish_count,
    currentLightIntensity: payload.current_light_intensity,
    lastTelemetryAt: normalizeText(payload.last_telemetry_at),
    lastStatusAt: normalizeText(payload.last_status_at),
    lastCommandAt: normalizeText(payload.last_command_at),
    lastCommand: normalizeText(payload.last_command),
  };
}

function mapLog(payload: SimulatorLogPayload): SimulatorLogEntry {
  return {
    createdAt: payload.created_at,
    level: payload.level,
    message: payload.message,
  };
}

export async function getSimulatorConfig(): Promise<SimulatorBrokerConfig> {
  const payload = await http.get<SimulatorBrokerConfigPayload>("/simulator/config");
  return mapConfig(payload);
}

export async function updateSimulatorConfig(
  config: SimulatorConfigInput,
): Promise<SimulatorBrokerConfig> {
  const payload = await http.put<SimulatorBrokerConfigPayload>("/simulator/config", config);
  return mapConfig(payload);
}

export async function getSimulatorDevices(): Promise<SimulatorDevice[]> {
  const payload = await http.get<SimulatorDevicePayload[]>("/simulator/devices");
  return payload.map(mapDevice);
}

export async function createSimulatorDevice(
  input: SimulatorDeviceInput,
): Promise<SimulatorDevice> {
  const payload = await http.post<SimulatorDevicePayload>("/simulator/devices", {
    device_code: input.deviceCode,
    device_name: input.deviceName,
    location: input.location || null,
    status: "offline",
    base_light: input.baseLight,
    variance: input.variance,
    voltage_base: input.voltageBase,
    telemetry_enabled: input.telemetryEnabled,
    telemetry_interval_seconds: input.telemetryIntervalSeconds,
    status_every: input.statusEvery,
    online: input.online,
    auto_start: input.autoStart,
  });
  return mapDevice(payload);
}

export async function startSimulatorDevice(deviceId: number): Promise<SimulatorDevice> {
  const payload = await http.post<SimulatorDevicePayload>(`/simulator/devices/${deviceId}/start`);
  return mapDevice(payload);
}

export async function stopSimulatorDevice(deviceId: number): Promise<SimulatorDevice> {
  const payload = await http.post<SimulatorDevicePayload>(`/simulator/devices/${deviceId}/stop`);
  return mapDevice(payload);
}

export async function deleteSimulatorDevice(deviceId: number): Promise<void> {
  await http.delete(`/simulator/devices/${deviceId}`);
}

export async function updateSimulatorDevice(
  deviceId: number,
  input: SimulatorDeviceUpdateInput,
): Promise<SimulatorDevice> {
  const payload = await http.put<SimulatorDevicePayload>(`/simulator/devices/${deviceId}`, {
    device_name: input.deviceName,
    location: input.location || null,
    base_light: input.baseLight,
    variance: input.variance,
    voltage_base: input.voltageBase,
    telemetry_enabled: input.telemetryEnabled,
    telemetry_interval_seconds: input.telemetryIntervalSeconds,
    status_every: input.statusEvery,
    online: input.online,
    running: input.running,
  });
  return mapDevice(payload);
}

export async function getSimulatorLogs(
  limit = 120,
  level?: string,
): Promise<SimulatorLogEntry[]> {
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
