import { mockDashboardOverview } from "@/mock/data";
import type { DashboardOverview } from "@/types/models";

function delay(ms = 180) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  await delay();
  return structuredClone(mockDashboardOverview);
}
