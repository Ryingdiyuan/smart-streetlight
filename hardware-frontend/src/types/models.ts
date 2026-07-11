export type DeviceStatus = "online" | "offline";
export type LampStatus = "ON" | "OFF";
export type AlarmLevel = "INFO" | "WARN" | "CRITICAL";
export type AlarmType = "DEVICE_OFFLINE" | "LIGHT_ABNORMAL" | "COMMAND_FAILED";
export type CommandType = "TURN_ON" | "TURN_OFF" | "SET_BRIGHTNESS";
export type CommandSource = "manual" | "auto";

export interface Device {
  id: number;
  deviceCode: string;
  deviceName: string;
  location: string;
  latitude?: number;
  longitude?: number;
  status: DeviceStatus;
  lampStatus: LampStatus;
  lastHeartbeatAt: string;
}

export interface ThresholdConfig {
  deviceId: string;
  lowThreshold: number;
  highThreshold: number;
  enabled: boolean;
}

export interface LightHistoryPoint {
  timestamp: string;
  lightIntensity: number;
  lampStatus: LampStatus;
}

export interface CommandLog {
  id: string;
  deviceId: string;
  command: CommandType;
  source: CommandSource;
  result: "pending" | "success" | "failed" | "skipped";
  createdAt: string;
}

export interface BatchCommandResult {
  deviceId: number;
  deviceCode: string;
  result: CommandLog["result"];
  logId: string;
  createdAt: string;
}

export interface BatchCommandSummary {
  command: CommandType;
  total: number;
  successCount: number;
  failedCount: number;
  skippedCount: number;
  results: BatchCommandResult[];
}

export interface AlarmRecord {
  id: string;
  deviceId: string;
  alarmType: AlarmType;
  alarmLevel: AlarmLevel;
  alarmContent: string;
  handled: boolean;
  createdAt: string;
}

export interface DeviceDetail extends Device {
  currentLightIntensity: number;
  threshold: ThresholdConfig;
  history: LightHistoryPoint[];
  commandLogs: CommandLog[];
  alarms: AlarmRecord[];
}

export interface DashboardStat {
  label: string;
  value: string;
  helper: string;
}

export interface DashboardOverview {
  stats: DashboardStat[];
  latestAlarms: AlarmRecord[];
  featuredDevice: Pick<Device, "deviceCode" | "deviceName" | "status" | "lampStatus">;
  featuredHistory: LightHistoryPoint[];
  devices: Device[];
  recentCommands: CommandLog[];
}

export interface LoginPayload {
  username: string;
  password: string;
}

export type UserRole = "admin" | "maintainer" | "user";

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
  is_active?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

export interface AgentMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface AgentPromptOption {
  id: string;
  title: string;
}

export interface AgentQuestionOptions {
  deviceId?: number;
  deviceCode?: string;
}

export interface RealtimeLightReading {
  deviceId: number;
  deviceCode: string;
  deviceName: string;
  location: string;
  status: DeviceStatus;
  lampStatus: LampStatus;
  lightIntensity: number;
  updatedAt: string;
}

export interface SimulatorBrokerConfig {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password: string;
  clientId: string;
  connected: boolean;
}

export interface SimulatorSensor {
  sensorId: number;
  sensorCode: string;
  sensorName: string;
  location: string;
  running: boolean;
  online: boolean;
  systemStatus: DeviceStatus;
  lampStatus: "on" | "off";
  brightness: number;
  baseLight: number;
  variance: number;
  voltageBase: number;
  telemetryEnabled: boolean;
  telemetryIntervalSeconds: number;
  statusEvery: number;
  publishCount: number;
  currentLightIntensity: number;
  lastTelemetryAt: string;
  lastStatusAt: string;
  lastCommandAt: string;
  lastCommand: string;
  boundDeviceId?: number;
  boundDeviceCode?: string;
  boundDeviceName?: string;
  controlMode?: "manual" | "auto";
}

export interface SimulatorLogEntry {
  createdAt: string;
  level: string;
  message: string;
}
