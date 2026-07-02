import { isMockServiceEnabled, runtimeConfig } from "@/config/env";

export function createServiceSwitcher<T>(mockImpl: T, apiImpl: T): T {
  return (isMockServiceEnabled ? mockImpl : apiImpl) as T;
}

export function getCurrentServiceModeLabel() {
  return runtimeConfig.serviceMode === "mock" ? "Mock" : "API";
}
