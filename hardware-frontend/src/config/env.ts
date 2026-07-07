const serviceMode = import.meta.env.VITE_SERVICE_MODE ?? "api";

export const runtimeConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api",
  serviceMode: serviceMode === "api" ? "api" : "mock",
};

export const isMockServiceEnabled = runtimeConfig.serviceMode === "mock";
