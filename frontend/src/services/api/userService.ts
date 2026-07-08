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

export function getUserList(search?: string) {
  const params = search ? `?search=${encodeURIComponent(search)}` : "";
  return http.get<AuthUser[]>(`/users${params}`);
}

export function createUser(payload: UserCreatePayload) {
  return http.post<AuthUser>("/users", payload);
}

export function updateUser(userId: number, payload: UserUpdatePayload) {
  return http.put<AuthUser>(`/users/${userId}`, payload);
}

export function deleteUser(userId: number) {
  return http.delete<void>(`/users/${userId}`);
}
