import type { LightHistoryPoint, RealtimeLightReading } from "@/types/models";

import { http } from "@/lib/http";
import { getDeviceList } from "@/services/api/deviceService";
import {
  type LightDataApiPayload,
  isHttpStatus,
  mapLampStatus,
  mapLightHistoryPoint,
} from "@/services/api/normalizers";

export interface LightHistoryQueryOptions {
  startTime?: string;
  endTime?: string;
  limit?: number;
}

async function getLatestLight(deviceId: number) {
  try {
    return await http.get<LightDataApiPayload>(`/devices/${deviceId}/latest-light`);
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return null;
    }
    throw error;
  }
}

export async function getRealtimeLightReadings(): Promise<RealtimeLightReading[]> {
  const devices = await getDeviceList();
  const latestResults = await Promise.allSettled(
    devices.map((device) => getLatestLight(device.id)),
  );

  return devices.map((device, index) => {
    const latestResult = latestResults[index];
    if (latestResult.status !== "fulfilled" || !latestResult.value) {
      return {
        deviceId: device.id,
        deviceCode: device.deviceCode,
        deviceName: device.deviceName,
        location: device.location,
        status: device.status,
        lampStatus: device.lampStatus,
        lightIntensity: 0,
        updatedAt: device.lastHeartbeatAt,
      };
    }

    return {
      deviceId: device.id,
      deviceCode: device.deviceCode,
      deviceName: device.deviceName,
      location: device.location,
      status: device.status,
      lampStatus: mapLampStatus(latestResult.value.lamp_status),
      lightIntensity: latestResult.value.light_intensity,
      updatedAt: latestResult.value.reported_at.replace("T", " ").slice(0, 19),
    };
  });
}

export async function getLightHistory(
  deviceId: number,
  options: LightHistoryQueryOptions = {},
): Promise<LightHistoryPoint[]> {
  try {
    const searchParams = new URLSearchParams();
    if (options.startTime) {
      searchParams.set("start_time", options.startTime);
    }
    if (options.endTime) {
      searchParams.set("end_time", options.endTime);
    }
    if (options.limit) {
      searchParams.set("limit", String(options.limit));
    }

    const query = searchParams.toString();
    const history = await http.get<LightDataApiPayload[]>(
      `/devices/${deviceId}/light-history${query ? `?${query}` : ""}`,
    );
    return history.slice().reverse().map(mapLightHistoryPoint);
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return [];
    }
    throw error;
  }
}

export async function getAllDevicesLightHistory(): Promise<Record<number, LightHistoryPoint[]>> {
  const devices = await getDeviceList();
  const historyEntries = await Promise.all(
    devices.map(async (device) => [device.id, await getLightHistory(device.id)] as const),
  );

  return Object.fromEntries(historyEntries);
}
