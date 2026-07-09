import { getAuthSession } from "@/services/authStorage";
import type { UserRole } from "@/types/models";

export type Permission =
  | "viewDashboard"
  | "viewDevices"
  | "operateDevices"
  | "handleAlarms"
  | "viewAgent";

export const roleLabels: Record<UserRole, string> = {
  admin: "管理员",
  maintainer: "运维人员",
  user: "查看者",
};

const rolePermissions: Record<UserRole, Permission[]> = {
  admin: ["viewDashboard", "viewDevices", "operateDevices", "handleAlarms", "viewAgent"],
  maintainer: ["viewDashboard", "viewDevices", "operateDevices", "handleAlarms", "viewAgent"],
  user: ["viewDashboard", "viewDevices", "viewAgent"],
};

export function getCurrentRole(): UserRole | null {
  return getAuthSession()?.user.role ?? null;
}

export function getRoleLabel(role = getCurrentRole()) {
  return role ? roleLabels[role] : "未登录";
}

export function can(permission: Permission, role = getCurrentRole()) {
  return Boolean(role && rolePermissions[role]?.includes(permission));
}
