import type {
  AlarmLevel,
  AlarmRecord,
  BatchCommandResult,
  BatchCommandSummary,
  AlarmType,
  CommandLog,
  Device,
  DeviceStatus,
  LampStatus,
  LightHistoryPoint,
  ThresholdConfig,
} from "@/types/models";

export interface DeviceApiPayload {
  id: number;
  device_code: string;
  device_name: string;
  location: string | null;
  latitude?: number | null;
  longitude?: number | null;
  status: string;
  last_heartbeat_at?: string | null;
}

export interface LightDataApiPayload {
  id: number;
  device_id: number;
  light_intensity: number;
  lamp_status: string;
  voltage?: number | null;
  reported_at: string;
  created_at: string;
}

export interface ThresholdConfigApiPayload {
  id: number;
  device_id: number;
  low_threshold: number;
  high_threshold: number;
  enabled: boolean;
  updated_at: string;
}

export interface ControlLogApiPayload {
  id: number;
  device_id: number;
  command: string;
  source: string;
  result: string;
  request_payload?: Record<string, unknown> | null;
  reply_payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface BatchControlLogItemApiPayload {
  device_id: number;
  device_code: string;
  result: string;
  log_id: number;
  created_at: string;
}

export interface BatchControlLogApiPayload {
  command: string;
  total: number;
  success_count: number;
  failed_count: number;
  skipped_count: number;
  results: BatchControlLogItemApiPayload[];
}

export interface AlarmApiPayload {
  id: number;
  device_id: number;
  alarm_type: string;
  alarm_level: string;
  alarm_content: string;
  handled: boolean;
  handled_at?: string | null;
  created_at: string;
}

export interface AgentChatApiPayload {
  answer: string;
  source: string;
  related_device?: {
    id: number;
    device_code: string;
    device_name: string;
  } | null;
  context_summary?: Record<string, unknown>;
}

export function isHttpStatus(error: unknown, status: number): boolean {
  return typeof error === "object" && error !== null && "status" in error && error.status === status;
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "--";
  }

  return value.replace("T", " ").slice(0, 19);
}

export function mapDeviceStatus(status: string): DeviceStatus {
  return status === "online" ? "online" : "offline";
}

export function mapLampStatus(status?: string | null): LampStatus {
  return String(status ?? "").toUpperCase() === "ON" ? "ON" : "OFF";
}

export function mapAlarmLevel(level: string): AlarmLevel {
  const normalized = level.toUpperCase();
  if (normalized === "CRITICAL") {
    return "CRITICAL";
  }
  if (normalized === "WARN" || normalized === "WARNING") {
    return "WARN";
  }
  return "INFO";
}

export function mapAlarmType(type: string): AlarmType {
  const normalized = type.toUpperCase();
  if (normalized === "COMMAND_FAILED") {
    return "COMMAND_FAILED";
  }
  if (normalized === "LIGHT_ABNORMAL") {
    return "LIGHT_ABNORMAL";
  }
  return "DEVICE_OFFLINE";
}

export function mapCommandResult(result: string): CommandLog["result"] {
  const normalized = result.toLowerCase();
  if (normalized === "pending") {
    return "pending";
  }
  if (normalized === "failed") {
    return "failed";
  }
  if (normalized === "skipped") {
    return "skipped";
  }
  return "success";
}

export function mapCommandSource(source: string): CommandLog["source"] {
  return source === "auto" ? "auto" : "manual";
}

export function mapDevicePayload(payload: DeviceApiPayload): Device {
  return {
    id: payload.id,
    deviceCode: payload.device_code,
    deviceName: payload.device_name,
    location: payload.location ?? "-",
    latitude: payload.latitude ?? undefined,
    longitude: payload.longitude ?? undefined,
    status: mapDeviceStatus(payload.status),
    lampStatus: "OFF",
    lastHeartbeatAt: formatDateTime(payload.last_heartbeat_at),
  };
}

export function mapLightHistoryPoint(payload: LightDataApiPayload): LightHistoryPoint {
  return {
    timestamp: formatDateTime(payload.reported_at),
    lightIntensity: payload.light_intensity,
    lampStatus: mapLampStatus(payload.lamp_status),
  };
}

export function mapThresholdPayload(
  payload: ThresholdConfigApiPayload,
  deviceCode?: string,
): ThresholdConfig {
  return {
    deviceId: deviceCode ?? String(payload.device_id),
    lowThreshold: payload.low_threshold,
    highThreshold: payload.high_threshold,
    enabled: payload.enabled,
  };
}

export function mapCommandLogPayload(
  payload: ControlLogApiPayload,
  deviceCode?: string,
): CommandLog {
  return {
    id: String(payload.id),
    deviceId: deviceCode ?? String(payload.device_id),
    command: payload.command.toUpperCase() as CommandLog["command"],
    source: mapCommandSource(payload.source),
    result: mapCommandResult(payload.result),
    createdAt: formatDateTime(payload.created_at),
  };
}

export function mapBatchCommandResultPayload(
  payload: BatchControlLogItemApiPayload,
): BatchCommandResult {
  return {
    deviceId: payload.device_id,
    deviceCode: payload.device_code,
    result: mapCommandResult(payload.result),
    logId: String(payload.log_id),
    createdAt: formatDateTime(payload.created_at),
  };
}

export function mapBatchCommandSummaryPayload(
  payload: BatchControlLogApiPayload,
): BatchCommandSummary {
  return {
    command: payload.command.toUpperCase() as BatchCommandSummary["command"],
    total: payload.total,
    successCount: payload.success_count,
    failedCount: payload.failed_count,
    skippedCount: payload.skipped_count,
    results: payload.results.map(mapBatchCommandResultPayload),
  };
}

export function mapAlarmPayload(payload: AlarmApiPayload, deviceCode?: string): AlarmRecord {
  return {
    id: String(payload.id),
    deviceId: deviceCode ?? String(payload.device_id),
    alarmType: mapAlarmType(payload.alarm_type),
    alarmLevel: mapAlarmLevel(payload.alarm_level),
    alarmContent: payload.alarm_content,
    handled: payload.handled,
    createdAt: formatDateTime(payload.created_at),
  };
}
