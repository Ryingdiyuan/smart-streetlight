import { mockDeviceDetails, mockDevices } from "@/mock/data";
import type {
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

export async function updateDevice(
  id: number,
  data: { latitude?: number; longitude?: number; device_name?: string; location?: string },
): Promise<Device> {
  await delay();
  const device = mockDevices.find((d) => d.id === id);
  if (!device) throw new Error("设备不存在");
  if (data.latitude !== undefined) device.latitude = data.latitude;
  if (data.longitude !== undefined) device.longitude = data.longitude;
  if (data.device_name) device.deviceName = data.device_name;
  if (data.location !== undefined) device.location = data.location;

  // Also update in mockDeviceDetails
  const detail = mockDeviceDetails[id];
  if (detail) {
    if (data.latitude !== undefined) detail.latitude = data.latitude;
    if (data.longitude !== undefined) detail.longitude = data.longitude;
  }

  return structuredClone(device);
}
