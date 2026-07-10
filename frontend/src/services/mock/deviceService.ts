import { mockDeviceDetails, mockDevices } from "@/mock/data";
import type {
  BatchCommandSummary,
  CommandLog,
  Device,
  DeviceDetail,
  ThresholdConfig,
} from "@/types/models";

function delay(ms = 180) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getDeviceList(): Promise<Device[]> {
  await delay();
  return structuredClone(mockDevices);
}

export async function getDeviceDetail(id: number): Promise<DeviceDetail | null> {
  await delay();
  const detail = mockDeviceDetails[id];
  return detail ? structuredClone(detail) : null;
}

export async function updateDeviceThreshold(
  id: number,
  threshold: ThresholdConfig,
): Promise<ThresholdConfig> {
  await delay();
  mockDeviceDetails[id].threshold = { ...threshold };
  return structuredClone(mockDeviceDetails[id].threshold);
}

export async function sendDeviceCommand(
  id: number,
  command: "TURN_ON" | "TURN_OFF",
): Promise<CommandLog> {
  await delay();
  const newLog: CommandLog = {
    id: `CMD-${Date.now()}`,
    deviceId: mockDeviceDetails[id].deviceCode,
    command,
    source: "manual",
    result: "success",
    createdAt: new Date().toLocaleString("zh-CN", { hour12: false }),
  };

  mockDeviceDetails[id].lampStatus = command === "TURN_ON" ? "ON" : "OFF";
  mockDeviceDetails[id].commandLogs = [newLog, ...mockDeviceDetails[id].commandLogs];

  const listItem = mockDevices.find((item) => item.id === id);
  if (listItem) {
    listItem.lampStatus = mockDeviceDetails[id].lampStatus;
  }

  return structuredClone(newLog);
}

export async function sendBatchDeviceCommand(
  deviceIds: number[],
  command: "TURN_ON" | "TURN_OFF",
): Promise<BatchCommandSummary> {
  await delay();

  const uniqueIds = [...new Set(deviceIds)];
  const createdAt = new Date().toLocaleString("zh-CN", { hour12: false });
  const results = uniqueIds.map((id, index) => {
    const detail = mockDeviceDetails[id];
    if (!detail) {
      throw new Error(`设备不存在: ${id}`);
    }

    const newLog: CommandLog = {
      id: `CMD-${Date.now()}-${index}`,
      deviceId: detail.deviceCode,
      command,
      source: "manual",
      result: "success",
      createdAt,
    };

    detail.lampStatus = command === "TURN_ON" ? "ON" : "OFF";
    detail.commandLogs = [newLog, ...detail.commandLogs];

    const listItem = mockDevices.find((item) => item.id === id);
    if (listItem) {
      listItem.lampStatus = detail.lampStatus;
    }

    return {
      deviceId: id,
      deviceCode: detail.deviceCode,
      result: "success" as const,
      logId: newLog.id,
      createdAt,
    };
  });

  return structuredClone({
    command,
    total: uniqueIds.length,
    successCount: uniqueIds.length,
    failedCount: 0,
    skippedCount: 0,
    results,
  });
}

export async function createDevice(data: {
  device_code: string;
  device_name: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  sensor_id?: number;
  control_mode?: "manual" | "auto";
}): Promise<Device> {
  await delay();

  if (mockDevices.some((device) => device.deviceCode === data.device_code)) {
    throw new Error("设备编码已存在");
  }

  const nextId = mockDevices.length ? Math.max(...mockDevices.map((device) => device.id)) + 1 : 1;
  const createdDevice: Device = {
    id: nextId,
    deviceCode: data.device_code,
    deviceName: data.device_name,
    location: data.location ?? "-",
    latitude: data.latitude,
    longitude: data.longitude,
    status: "offline",
    lampStatus: "OFF",
    lastHeartbeatAt: "--",
    controlMode: data.control_mode ?? "manual",
    sensorId: data.sensor_id,
  };

  const createdDetail: DeviceDetail = {
    ...createdDevice,
    currentLightIntensity: 0,
    threshold: {
      deviceId: createdDevice.deviceCode,
      lowThreshold: 100,
      highThreshold: 300,
      enabled: true,
    },
    history: [],
    commandLogs: [],
    alarms: [],
  };

  mockDevices.push(createdDevice);
  mockDeviceDetails[nextId] = createdDetail;
  return structuredClone(createdDevice);
}

export async function updateDevice(
  id: number,
  data: {
    latitude?: number;
    longitude?: number;
    device_name?: string;
    location?: string;
    sensor_id?: number;
    control_mode?: "manual" | "auto";
  },
): Promise<Device> {
  await delay();
  const device = mockDevices.find((d) => d.id === id);
  if (!device) throw new Error("设备不存在");
  if (data.latitude !== undefined) device.latitude = data.latitude;
  if (data.longitude !== undefined) device.longitude = data.longitude;
  if (data.device_name) device.deviceName = data.device_name;
  if (data.location !== undefined) device.location = data.location;
  if (data.sensor_id !== undefined) device.sensorId = data.sensor_id;
  if (data.control_mode !== undefined) device.controlMode = data.control_mode;

  // Also update in mockDeviceDetails
  const detail = mockDeviceDetails[id];
  if (detail) {
    if (data.latitude !== undefined) detail.latitude = data.latitude;
    if (data.longitude !== undefined) detail.longitude = data.longitude;
    if (data.sensor_id !== undefined) detail.sensorId = data.sensor_id;
    if (data.control_mode !== undefined) detail.controlMode = data.control_mode;
  }

  return structuredClone(device);
}
