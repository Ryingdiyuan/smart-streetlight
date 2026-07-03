import * as apiService from "@/services/api/lightService";
import * as mockService from "@/services/mock/lightService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const {
  getRealtimeLightReadings,
  getLightHistory,
  getAllDevicesLightHistory,
} = createServiceSwitcher(mockService, apiService);
