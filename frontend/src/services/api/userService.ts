import { http } from "@/lib/http";
import type { AuthUser, UserRole } from "@/types/models";

export interface UserCreatePayload {
  username: string;
  password: string;
  role: UserRole;
  is_active: boolean;
}

export interface UserUpdatePayload {
  username?: string;
  password?: string;
  role?: UserRole;
  is_active?: boolean;
}

export function getUserList() {
  return http.get<AuthUser[]>("/users");
}

export function createUser(payload: UserCreatePayload) {
  return http.post<AuthUser>("/users", payload);
}

export function updateUser(userId: number, payload: UserUpdatePayload) {
  return http.put<AuthUser>(`/users/${userId}`, payload);
}
