import * as apiService from "@/services/api/alarmService";
import * as mockService from "@/services/mock/alarmService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const { getAlarmList } = createServiceSwitcher(mockService, apiService);
