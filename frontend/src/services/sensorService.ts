import * as apiService from "@/services/api/sensorService";
import * as mockService from "@/services/mock/sensorService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const { getSensorList } = createServiceSwitcher(mockService, apiService);
