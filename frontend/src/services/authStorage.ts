import type { AuthSession } from "@/types/models";

const AUTH_STORAGE_KEY = "smart-streetlight-auth";

export function saveAuthSession(session: AuthSession) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function getAuthSession(): AuthSession | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function getAccessToken() {
  return getAuthSession()?.token ?? "";
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}
