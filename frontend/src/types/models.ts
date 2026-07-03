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
  result: "pending" | "success" | "failed";
  createdAt: string;
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

export interface AgentMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface AgentPromptOption {
  id: string;
  title: string;
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
