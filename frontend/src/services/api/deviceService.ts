import { http } from "@/lib/http";
import type {
  BatchCommandSummary,
  CommandLog,
  ControlMode,
  Device,
  DeviceDetail,
  ThresholdConfig,
} from "@/types/models";

import {
  type AlarmApiPayload,
  type BatchControlLogApiPayload,
  type ControlLogApiPayload,
  type DeviceApiPayload,
  type LightDataApiPayload,
  type ThresholdConfigApiPayload,
  isHttpStatus,
  mapAlarmPayload,
  mapBatchCommandSummaryPayload,
  mapCommandLogPayload,
  mapDevicePayload,
  mapLampStatus,
  mapLightHistoryPoint,
  mapThresholdPayload,
} from "@/services/api/normalizers";

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

async function getLightHistory(deviceId: number) {
  try {
    return await http.get<LightDataApiPayload[]>(`/devices/${deviceId}/light-history`);
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return [];
    }
    throw error;
  }
}

async function getDeviceCommands(deviceId: number) {
  try {
    return await http.get<ControlLogApiPayload[]>(`/devices/${deviceId}/commands`);
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return [];
    }
    throw error;
  }
}

export async function getDeviceList(): Promise<Device[]> {
  const devices = await http.get<DeviceApiPayload[]>("/devices");
  const latestLightResults = await Promise.allSettled(
    devices.map((device) => getLatestLight(device.id)),
  );

  return devices.map((device, index) => {
    const mappedDevice = mapDevicePayload(device);
    const latestLightResult = latestLightResults[index];
    if (latestLightResult.status !== "fulfilled" || !latestLightResult.value) {
      return mappedDevice;
    }

    return {
      ...mappedDevice,
      lampStatus: mapLampStatus(latestLightResult.value.lamp_status),
      lastHeartbeatAt:
        mappedDevice.lastHeartbeatAt === "--"
          ? latestLightResult.value.reported_at.replace("T", " ").slice(0, 19)
          : mappedDevice.lastHeartbeatAt,
    };
  });
}

export async function getDeviceDetail(id: number): Promise<DeviceDetail | null> {
  try {
    const [devicePayload, latestLight, history, threshold, commandLogs, alarms] = await Promise.all([
      http.get<DeviceApiPayload>(`/devices/${id}`),
      getLatestLight(id),
      getLightHistory(id),
      http.get<ThresholdConfigApiPayload>(`/devices/${id}/threshold`),
      getDeviceCommands(id),
      http.get<AlarmApiPayload[]>("/alarms"),
    ]);

    const device = mapDevicePayload(devicePayload);

    return {
      ...device,
      lampStatus: latestLight ? mapLampStatus(latestLight.lamp_status) : device.lampStatus,
      currentLightIntensity: latestLight?.light_intensity ?? 0,
      threshold: mapThresholdPayload(threshold, device.deviceCode),
      history: history
        .slice()
        .reverse()
        .map(mapLightHistoryPoint),
      commandLogs: commandLogs.map((item) => mapCommandLogPayload(item, device.deviceCode)),
      alarms: alarms
        .filter((alarm) => alarm.device_id === id)
        .map((alarm) => mapAlarmPayload(alarm, device.deviceCode)),
    };
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return null;
    }

    throw error;
  }
}

export async function updateDeviceThreshold(
  id: number,
  threshold: ThresholdConfig,
): Promise<ThresholdConfig> {
  const payload = await http.put<ThresholdConfigApiPayload>(`/devices/${id}/threshold`, {
    low_threshold: threshold.lowThreshold,
    high_threshold: threshold.highThreshold,
    enabled: threshold.enabled,
  });

  return mapThresholdPayload(payload, threshold.deviceId);
}

export async function sendDeviceCommand(
  id: number,
  command: "TURN_ON" | "TURN_OFF",
): Promise<CommandLog> {
  const payload = await http.post<ControlLogApiPayload>(`/devices/${id}/commands`, {
    command,
  });

  return mapCommandLogPayload(payload);
}

export async function sendBatchDeviceCommand(
  deviceIds: number[],
  command: "TURN_ON" | "TURN_OFF",
): Promise<BatchCommandSummary> {
  const payload = await http.post<BatchControlLogApiPayload>("/devices/commands/batch", {
    device_ids: deviceIds,
    command,
  });

  return mapBatchCommandSummaryPayload(payload);
}

export interface CreateDevicePayload {
  device_code: string;
  device_name: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  sensor_id?: number;
  control_mode?: ControlMode;
}

export async function createDevice(data: CreateDevicePayload): Promise<Device> {
  const payload = await http.post<DeviceApiPayload>("/devices", data);
  return mapDevicePayload(payload);
}

export async function updateDevice(
  id: number,
  data: Partial<CreateDevicePayload>,
): Promise<Device> {
  const payload = await http.put<DeviceApiPayload>(`/devices/${id}`, data);
  return mapDevicePayload(payload);
}
