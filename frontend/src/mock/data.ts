import type {
  AgentMessage,
  AgentPromptOption,
  AlarmRecord,
  DashboardOverview,
  Device,
  DeviceDetail,
  LightHistoryPoint,
  RealtimeLightReading,
} from "@/types/models";

export const mockDevices: Device[] = [
  {
    id: 1,
    deviceCode: "SL-001",
    deviceName: "一号路灯",
    location: "校门口",
    status: "online",
    lampStatus: "ON",
    lastHeartbeatAt: "2026-07-02 09:56:12",
  },
  {
    id: 2,
    deviceCode: "SL-002",
    deviceName: "二号路灯",
    location: "教学楼前",
    status: "online",
    lampStatus: "OFF",
    lastHeartbeatAt: "2026-07-02 09:55:48",
  },
  {
    id: 3,
    deviceCode: "SL-003",
    deviceName: "三号路灯",
    location: "主干道东侧",
    status: "offline",
    lampStatus: "OFF",
    lastHeartbeatAt: "2026-07-02 09:40:11",
  },
];

export const mockAlarms: AlarmRecord[] = [
  {
    id: "ALM-001",
    deviceId: "SL-003",
    alarmType: "DEVICE_OFFLINE",
    alarmLevel: "WARN",
    alarmContent: "设备心跳超时，已判定离线",
    handled: false,
    createdAt: "2026-07-02 09:42:00",
  },
  {
    id: "ALM-002",
    deviceId: "SL-001",
    alarmType: "COMMAND_FAILED",
    alarmLevel: "INFO",
    alarmContent: "开灯指令执行超时，已自动重试",
    handled: true,
    createdAt: "2026-07-02 09:25:30",
  },
];

export const mockDashboardOverview: DashboardOverview = {
  stats: [
    { label: "设备总数", value: "12", helper: "已登记路灯设备" },
    { label: "在线设备", value: "9", helper: "支持后续实时刷新" },
    { label: "离线告警", value: "2", helper: "可与告警页联动" },
    { label: "当前开灯", value: "5", helper: "展示路灯状态" },
  ],
  latestAlarms: mockAlarms,
  featuredDevice: {
    deviceCode: mockDevices[0].deviceCode,
    deviceName: mockDevices[0].deviceName,
    status: mockDevices[0].status,
    lampStatus: mockDevices[0].lampStatus,
  },
  featuredHistory: [
    { timestamp: "09:00", lightIntensity: 68, lampStatus: "ON" },
    { timestamp: "09:10", lightIntensity: 76, lampStatus: "ON" },
    { timestamp: "09:20", lightIntensity: 86, lampStatus: "ON" },
    { timestamp: "09:30", lightIntensity: 101, lampStatus: "ON" },
    { timestamp: "09:40", lightIntensity: 118, lampStatus: "ON" },
    { timestamp: "09:50", lightIntensity: 128, lampStatus: "ON" },
  ],
  devices: mockDevices,
  recentCommands: [
    {
      id: "CMD-001",
      deviceId: "SL-001",
      command: "TURN_ON",
      source: "manual",
      result: "success",
      createdAt: "2026-07-02 09:20:00",
    },
    {
      id: "CMD-004",
      deviceId: "SL-002",
      command: "TURN_OFF",
      source: "auto",
      result: "success",
      createdAt: "2026-07-02 09:16:00",
    },
  ],
};

export const mockDeviceDetails: Record<number, DeviceDetail> = {
  1: {
    ...mockDevices[0],
    currentLightIntensity: 128,
    threshold: {
      deviceId: "SL-001",
      lowThreshold: 100,
      highThreshold: 300,
      enabled: true,
    },
    history: [
      { timestamp: "09:20", lightIntensity: 86, lampStatus: "ON" },
      { timestamp: "09:30", lightIntensity: 101, lampStatus: "ON" },
      { timestamp: "09:40", lightIntensity: 118, lampStatus: "ON" },
      { timestamp: "09:50", lightIntensity: 128, lampStatus: "ON" },
    ],
    commandLogs: [
      {
        id: "CMD-001",
        deviceId: "SL-001",
        command: "TURN_ON",
        source: "manual",
        result: "success",
        createdAt: "2026-07-02 09:20:00",
      },
      {
        id: "CMD-002",
        deviceId: "SL-001",
        command: "TURN_OFF",
        source: "auto",
        result: "pending",
        createdAt: "2026-07-02 08:55:00",
      },
    ],
    alarms: [mockAlarms[1]],
  },
  2: {
    ...mockDevices[1],
    currentLightIntensity: 362,
    threshold: {
      deviceId: "SL-002",
      lowThreshold: 110,
      highThreshold: 320,
      enabled: true,
    },
    history: [
      { timestamp: "09:20", lightIntensity: 290, lampStatus: "OFF" },
      { timestamp: "09:30", lightIntensity: 305, lampStatus: "OFF" },
      { timestamp: "09:40", lightIntensity: 330, lampStatus: "OFF" },
      { timestamp: "09:50", lightIntensity: 362, lampStatus: "OFF" },
    ],
    commandLogs: [],
    alarms: [],
  },
  3: {
    ...mockDevices[2],
    currentLightIntensity: 42,
    threshold: {
      deviceId: "SL-003",
      lowThreshold: 95,
      highThreshold: 280,
      enabled: false,
    },
    history: [
      { timestamp: "09:10", lightIntensity: 40, lampStatus: "OFF" },
      { timestamp: "09:20", lightIntensity: 41, lampStatus: "OFF" },
      { timestamp: "09:30", lightIntensity: 42, lampStatus: "OFF" },
      { timestamp: "09:40", lightIntensity: 42, lampStatus: "OFF" },
    ],
    commandLogs: [
      {
        id: "CMD-003",
        deviceId: "SL-003",
        command: "TURN_ON",
        source: "manual",
        result: "failed",
        createdAt: "2026-07-02 09:12:00",
      },
    ],
    alarms: [mockAlarms[0]],
  },
};

export const mockPromptOptions: AgentPromptOption[] = [
  { id: "p1", title: "SL-001 离线后应该怎么排查？" },
  { id: "p2", title: "光照正常但路灯未开启可能是什么原因？" },
  { id: "p3", title: "指令下发成功但设备没有响应怎么办？" },
];

export const mockAgentMessages: AgentMessage[] = [
  {
    id: "m1",
    role: "user",
    content: "设备离线之后应该先检查什么？",
  },
  {
    id: "m2",
    role: "assistant",
    content: "建议先检查设备供电、网络连接、MQTT 心跳上报以及现场传感器状态。",
  },
];

/** 生成指定天数内每 10 分钟一条的光照采样数据 */
function generateLightHistory(
  baseIntensity: number,
  days: number,
  startDate: string,
): LightHistoryPoint[] {
  const points: LightHistoryPoint[] = [];
  const start = new Date(startDate);
  const now = new Date();
  const msPerPoint = 10 * 60 * 1000; // 10 minutes

  // 模拟一天的光照曲线：白天高，夜晚低
  const getIntensity = (h: number, m: number): number => {
    // 6:00-18:00 为白天，光照较强；夜晚较弱
    const hour = h + m / 60;
    if (hour >= 6 && hour <= 18) {
      // 正弦曲线模拟日照
      const peak = 0.5 + 0.5 * Math.sin(((hour - 6) / 12) * Math.PI);
      return Math.round(baseIntensity * peak * (0.85 + Math.random() * 0.3));
    }
    // 夜晚微弱光照（路灯补光）
    return Math.round((20 + Math.random() * 40) * (baseIntensity / 100));
  };

  const totalPoints = days * 24 * 6; // 6 points per hour
  for (let i = 0; i < totalPoints; i++) {
    const t = new Date(start.getTime() + i * msPerPoint);
    if (t > now) break;
    const h = t.getHours();
    const m = t.getMinutes();
    const intensity = getIntensity(h, m);
    const isNight = h < 6 || h >= 18;
    points.push({
      timestamp: `${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")} ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`,
      lightIntensity: intensity,
      lampStatus: isNight ? "ON" : "OFF",
    });
  }
  return points;
}

/** 预生成 7 天历史数据 */
const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
const startStr = sevenDaysAgo.toISOString().slice(0, 16).replace("T", " ");

export const mockLightHistory: Record<number, LightHistoryPoint[]> = {
  1: generateLightHistory(280, 7, startStr),
  2: generateLightHistory(320, 7, startStr),
  3: generateLightHistory(180, 7, startStr),
};

/** 实时光照监测读数快照 */
export function generateRealtimeReadings(): RealtimeLightReading[] {
  return mockDevices.map((d) => {
    const detail = mockDeviceDetails[d.id];
    const base = detail?.currentLightIntensity ?? 100;
    // 模拟实时波动
    const variance = Math.round((Math.random() - 0.5) * 30);
    return {
      deviceId: d.id,
      deviceCode: d.deviceCode,
      deviceName: d.deviceName,
      location: d.location,
      status: d.status,
      lampStatus: d.lampStatus,
      lightIntensity: Math.max(0, base + variance),
      updatedAt: new Date().toLocaleString("zh-CN", { hour12: false }),
    };
  });
}
