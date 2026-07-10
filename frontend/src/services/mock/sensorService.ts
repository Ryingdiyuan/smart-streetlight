import type { SensorSummary } from "@/types/models";

function delay(ms = 120) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getSensorList(): Promise<SensorSummary[]> {
  await delay();
  return [];
}
