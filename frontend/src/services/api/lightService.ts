import { http } from "@/lib/http";
import type { LightHistoryPoint, RealtimeLightReading } from "@/types/models";

export async function getRealtimeLightReadings(): Promise<RealtimeLightReading[]> {
  return http.get<RealtimeLightReading[]>("/devices/light-realtime");
}

export async function getLightHistory(deviceId: number): Promise<LightHistoryPoint[]> {
  return http.get<LightHistoryPoint[]>(`/devices/${deviceId}/light-history`);
}

export async function getAllDevicesLightHistory(): Promise<Record<number, LightHistoryPoint[]>> {
  return http.get<Record<number, LightHistoryPoint[]>>("/devices/light-history/all");
}
