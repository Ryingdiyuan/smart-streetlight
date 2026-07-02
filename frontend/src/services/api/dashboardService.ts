import { http } from "@/lib/http";
import type { DashboardOverview } from "@/types/models";

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const [devices, alarms] = await Promise.all([
    http.get<DashboardOverview["devices"]>("/devices"),
    http.get<DashboardOverview["latestAlarms"]>("/alarms"),
  ]);

  const onlineCount = devices.filter((item) => item.status === "online").length;
  const lampOnCount = devices.filter((item) => item.lampStatus === "ON").length;
  const latestAlarms = alarms.slice(0, 5);
  const featuredDeviceItem = devices[0];
  const featuredDevice = devices[0] ?? {
    deviceCode: "--",
    deviceName: "暂无设备",
    status: "offline" as const,
    lampStatus: "OFF" as const,
  };
  const [featuredHistory, recentCommands] = featuredDeviceItem
    ? await Promise.all([
        http.get<DashboardOverview["featuredHistory"]>(
          `/devices/${featuredDeviceItem.id}/light-history`,
        ),
        http.get<DashboardOverview["recentCommands"]>(
          `/devices/${featuredDeviceItem.id}/commands`,
        ),
      ])
    : [[], []];

  return {
    stats: [
      { label: "设备总数", value: String(devices.length), helper: "来自真实接口" },
      { label: "在线设备", value: String(onlineCount), helper: "设备列表统计结果" },
      { label: "离线告警", value: String(alarms.filter((item) => !item.handled).length), helper: "来自告警列表" },
      { label: "当前开灯", value: String(lampOnCount), helper: "实时路灯状态统计" },
    ],
    latestAlarms,
    featuredDevice,
    featuredHistory,
    devices,
    recentCommands,
  };
}
