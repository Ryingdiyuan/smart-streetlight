import * as apiService from "@/services/api/deviceService";
import * as mockService from "@/services/mock/deviceService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const {
  getDeviceList,
  getDeviceDetail,
  updateDeviceThreshold,
  sendDeviceCommand,
  updateDevice,
} = createServiceSwitcher(mockService, apiService);
