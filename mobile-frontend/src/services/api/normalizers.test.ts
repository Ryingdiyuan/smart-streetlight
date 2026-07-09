import { describe, expect, it } from "vitest";
import {
  formatDateTime,
  mapAlarmPayload,
  mapCommandLogPayload,
  mapDevicePayload,
  mapThresholdPayload,
} from "@/services/api/normalizers";

describe("normalizers", () => {
  it("formats device payload", () => {
    expect(
      mapDevicePayload({
        id: 1,
        device_code: "SL-001",
        device_name: "一号路灯",
        location: null,
        status: "online",
        last_heartbeat_at: "2026-07-08T12:30:00",
      }),
    ).toEqual({
      id: 1,
      deviceCode: "SL-001",
      deviceName: "一号路灯",
      location: "未设置位置",
      status: "online",
      lampStatus: "OFF",
      lastHeartbeatAt: "2026-07-08 12:30:00",
    });
  });

  it("maps command and alarm payloads", () => {
    expect(
      mapCommandLogPayload({
        id: 2,
        device_id: 1,
        command: "turn_on",
        source: "manual",
        result: "success",
        created_at: "2026-07-08T12:30:00",
      }),
    ).toMatchObject({
      id: "2",
      deviceId: "1",
      command: "TURN_ON",
      result: "success",
    });

    expect(
      mapAlarmPayload(
        {
          id: 3,
          device_id: 1,
          alarm_type: "offline",
          alarm_level: "warning",
          alarm_content: "设备离线",
          handled: false,
          created_at: "2026-07-08T12:35:00",
        },
        "SL-001",
      ),
    ).toMatchObject({
      id: "3",
      deviceId: "SL-001",
      alarmType: "DEVICE_OFFLINE",
      alarmLevel: "WARN",
      handled: false,
    });
  });

  it("formats threshold and date", () => {
    expect(
      mapThresholdPayload({
        id: 1,
        device_id: 8,
        low_threshold: 25,
        high_threshold: 80,
        enabled: true,
      }),
    ).toEqual({
      deviceId: "8",
      lowThreshold: 25,
      highThreshold: 80,
      enabled: true,
    });

    expect(formatDateTime("2026-07-08T12:35:00")).toBe("2026-07-08 12:35:00");
    expect(formatDateTime(null)).toBe("--");
  });
});
