import { mockAlarms } from "@/mock/data";
import type { AlarmRecord } from "@/types/models";

function delay(ms = 160) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getAlarmList(): Promise<AlarmRecord[]> {
  await delay();
  return structuredClone(mockAlarms);
}

export async function handleAlarm(alarmId: string): Promise<AlarmRecord> {
  await delay();
  const target = mockAlarms.find((alarm) => alarm.id === alarmId);
  if (!target) {
    throw new Error("告警不存在");
  }

  target.handled = true;
  target.handledAt = new Date().toLocaleString("zh-CN", { hour12: false });
  return structuredClone(target);
}
