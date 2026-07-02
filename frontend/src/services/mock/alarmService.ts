import { mockAlarms } from "@/mock/data";
import type { AlarmRecord } from "@/types/models";

function delay(ms = 160) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getAlarmList(): Promise<AlarmRecord[]> {
  await delay();
  return structuredClone(mockAlarms);
}
