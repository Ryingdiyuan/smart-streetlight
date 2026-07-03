import { mockLightHistory, generateRealtimeReadings } from "@/mock/data";
import type { LightHistoryPoint, RealtimeLightReading } from "@/types/models";

function delay(ms = 180) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getRealtimeLightReadings(): Promise<RealtimeLightReading[]> {
  await delay(120);
  return generateRealtimeReadings();
}

export async function getLightHistory(deviceId: number): Promise<LightHistoryPoint[]> {
  await delay();
  return structuredClone(mockLightHistory[deviceId] ?? []);
}

export async function getAllDevicesLightHistory(): Promise<Record<number, LightHistoryPoint[]>> {
  await delay(200);
  return structuredClone(mockLightHistory);
}
