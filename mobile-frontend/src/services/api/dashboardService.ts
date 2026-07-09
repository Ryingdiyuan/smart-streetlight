import type { DashboardOverview } from "@/types/models";
import { getAlarmList } from "@/services/api/alarmService";
import { getDeviceList } from "@/services/api/deviceService";
import { getLightHistory, getRealtimeLightReadings } from "@/services/api/lightService";
import { http } from "@/lib/http";
import { type ControlLogApiPayload, isHttpStatus, mapCommandLogPayload } from "@/services/api/normalizers";

async function getRecentCommands(deviceId: number, deviceCode: string) {
  try {
    const logs = await http.get<ControlLogApiPayload[]>(`/devices/${deviceId}/commands?limit=5`);
    return logs.map((item) => mapCommandLogPayload(item, deviceCode));
  } catch (error) {
    if (isHttpStatus(error, 404)) {
      return [];
    }
    throw error;
  }
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const [devices, readings, latestAlarms] = await Promise.all([
    getDeviceList(),
    getRealtimeLightReadings(),
    getAlarmList(),
  ]);

  const readingByDeviceId = new Map(readings.map((reading) => [reading.deviceId, reading]));
  const enrichedDevices = devices.map((device) => {
    const reading = readingByDeviceId.get(device.id);
    if (!reading) {
      return device;
    }

    return {
      ...device,
      lampStatus: reading.lampStatus,
      lastHeartbeatAt: reading.updatedAt || device.lastHeartbeatAt,
    };
  });

  const onlineCount = enrichedDevices.filter((item) => item.status === "online").length;
  const lampOnCount = enrichedDevices.filter((item) => item.lampStatus === "ON").length;
  const latestUnhandled = latestAlarms.filter((item) => !item.handled);
  const featuredDevice = enrichedDevices[0] ?? {
    deviceCode: "--",
    deviceName: "暂无设备",
    status: "offline" as const,
    lampStatus: "OFF" as const,
  };

  const [featuredHistory, recentCommandsByDevice] =
    enrichedDevices.length > 0
      ? await Promise.all([
          getLightHistory(enrichedDevices[0].id).catch(() => []),
          Promise.all(enrichedDevices.map((device) => getRecentCommands(device.id, device.deviceCode).catch(() => []))),
        ])
      : [[], []];

  const prioritizedAlarms = latestAlarms
    .slice()
    .sort((left, right) => {
      if (left.handled !== right.handled) {
        return Number(left.handled) - Number(right.handled);
      }
      return right.createdAt.localeCompare(left.createdAt);
    });

  const recentCommands = recentCommandsByDevice
    .flat()
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
    .slice(0, 4);

  return {
    stats: [
      { label: "设备总数", value: String(enrichedDevices.length), helper: "移动端实时同步" },
      { label: "在线设备", value: String(onlineCount), helper: "设备状态实时统计" },
      { label: "未处理告警", value: String(latestUnhandled.length), helper: "需优先关注" },
      { label: "当前开灯", value: String(lampOnCount), helper: "基于最新光照上报" },
    ],
    latestAlarms: prioritizedAlarms.slice(0, 4),
    featuredDevice,
    featuredHistory,
    devices: enrichedDevices,
    recentCommands,
  };
}
