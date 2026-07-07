import { http } from "@/lib/http";
import type { AuthUser, LoginPayload, LoginResponse } from "@/types/models";

export function login(payload: LoginPayload) {
  return http.post<LoginResponse>("/auth/login", payload);
}

export function getCurrentUser() {
  return http.get<AuthUser>("/auth/me");
}
