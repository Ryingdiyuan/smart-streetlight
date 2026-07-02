import { http } from "@/lib/http";
import type { AlarmRecord } from "@/types/models";

export async function getAlarmList(): Promise<AlarmRecord[]> {
  return http.get<AlarmRecord[]>("/alarms");
}
