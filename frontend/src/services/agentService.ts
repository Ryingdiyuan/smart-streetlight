import * as apiService from "@/services/api/agentService";
import * as mockService from "@/services/mock/agentService";
import { createServiceSwitcher } from "@/services/serviceRuntime";

export const { getPromptOptions, getConversation, sendQuestion } = createServiceSwitcher(
  mockService,
  apiService,
);
