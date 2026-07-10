import { http } from "@/lib/http";
import { type SensorApiPayload, mapSensorPayload } from "@/services/api/normalizers";
import type { SensorSummary } from "@/types/models";

export async function getSensorList(options: { onlyUnbound?: boolean; onlyOnline?: boolean } = {}): Promise<SensorSummary[]> {
  const query = new URLSearchParams();
  if (options.onlyUnbound) {
    query.set("only_unbound", "true");
  }
  if (options.onlyOnline) {
    query.set("only_online", "true");
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const payload = await http.get<SensorApiPayload[]>(`/sensors${suffix}`);
  return payload.map(mapSensorPayload);
}
