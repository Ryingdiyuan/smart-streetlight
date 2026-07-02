import * as apiService from "@/services/api/dashboardService";
import * as mockService from "@/services/mock/dashboardService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const { getDashboardOverview } = createServiceSwitcher(mockService, apiService);
