import { http } from "@/lib/http";
import type {
  CommandLog,
  Device,
  DeviceDetail,
  LightHistoryPoint,
  ThresholdConfig,
} from "@/types/models";

interface LatestLightPayload {
  lightIntensity?: number;
  currentLightIntensity?: number;
  lampStatus?: Device["lampStatus"];
}

export async function getDeviceList(): Promise<Device[]> {
  return http.get<Device[]>("/devices");
}

export async function getDeviceDetail(id: number): Promise<DeviceDetail | null> {
  try {
    const [device, latestLight, history, threshold, commandLogs, alarms] = await Promise.all([
      http.get<Device>(`/devices/${id}`),
      http.get<LatestLightPayload>(`/devices/${id}/latest-light`),
      http.get<LightHistoryPoint[]>(`/devices/${id}/light-history`),
      http.get<ThresholdConfig>(`/devices/${id}/threshold`),
      http.get<CommandLog[]>(`/devices/${id}/commands`),
      http.get<DeviceDetail["alarms"]>("/alarms"),
    ]);

    return {
      ...device,
      lampStatus: latestLight.lampStatus ?? device.lampStatus,
      currentLightIntensity:
        latestLight.currentLightIntensity ?? latestLight.lightIntensity ?? 0,
      threshold,
      history,
      commandLogs,
      alarms: alarms.filter((alarm) => alarm.deviceId === device.deviceCode),
    };
  } catch (error) {
    if (error instanceof Error && /404/.test(error.message)) {
      return null;
    }

    throw error;
  }
}

export async function updateDeviceThreshold(
  id: number,
  threshold: ThresholdConfig,
): Promise<ThresholdConfig> {
  return http.put<ThresholdConfig>(`/devices/${id}/threshold`, threshold);
}

export async function sendDeviceCommand(
  id: number,
  command: "TURN_ON" | "TURN_OFF",
): Promise<CommandLog> {
  return http.post<CommandLog>(`/devices/${id}/commands`, {
    command,
    source: "manual",
  });
}
