import { http } from "@/lib/http";
import type { AlarmRecord } from "@/types/models";

import { getDeviceList } from "@/services/api/deviceService";
import { type AlarmApiPayload, mapAlarmPayload } from "@/services/api/normalizers";

export async function getAlarmList(): Promise<AlarmRecord[]> {
  const [alarms, devices] = await Promise.all([
    http.get<AlarmApiPayload[]>("/alarms"),
    getDeviceList(),
  ]);

  const deviceCodeById = new Map(devices.map((device) => [device.id, device.deviceCode]));

  return alarms.map((alarm) => mapAlarmPayload(alarm, alarm.device_id != null ? deviceCodeById.get(alarm.device_id) : undefined));
}

export async function handleAlarm(alarmId: string): Promise<AlarmRecord> {
  const [alarm, devices] = await Promise.all([
    http.put<AlarmApiPayload>(`/alarms/${alarmId}/handle`),
    getDeviceList(),
  ]);

  const deviceCodeById = new Map(devices.map((device) => [device.id, device.deviceCode]));
  return mapAlarmPayload(alarm, alarm.device_id != null ? deviceCodeById.get(alarm.device_id) : undefined);
}
