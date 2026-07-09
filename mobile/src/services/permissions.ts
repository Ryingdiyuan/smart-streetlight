import type { UserRole } from "@/types/models";
import { getAccessToken } from "@/lib/http";

export type Permission =
  | "viewDashboard"
  | "viewDevices"
  | "operateDevices"
  | "manageDeviceRegistry"
  | "handleAlarms"
  | "viewAgent"
  | "manageSimulator"
  | "manageUsers";

export const allRoles: UserRole[] = ["admin", "maintainer", "user"];

export const roleLabels: Record<UserRole, string> = {
  admin: "管理员",
  maintainer: "维修人员",
  user: "普通用户",
};

const rolePermissions: Record<UserRole, Permission[]> = {
  admin: [
    "viewDashboard",
    "viewDevices",
    "operateDevices",
    "manageDeviceRegistry",
    "handleAlarms",
    "viewAgent",
    "manageSimulator",
    "manageUsers",
  ],
  maintainer: [
    "viewDashboard",
    "viewDevices",
    "operateDevices",
    "handleAlarms",
    "viewAgent",
  ],
  user: ["viewDashboard", "viewDevices", "viewAgent"],
};

function getCurrentRoleFromToken(): UserRole | null {
  try {
    const raw = uni.getStorageSync("smart-streetlight-auth");
    if (!raw) return null;
    const session = JSON.parse(raw) as { user: { role: UserRole } };
    return session.user?.role ?? null;
  } catch {
    return null;
  }
}

export function getCurrentRole(): UserRole | null {
  return getCurrentRoleFromToken();
}

export function getRoleLabel(role?: UserRole | null) {
  return role && roleLabels[role] ? roleLabels[role] : "未登录";
}

export function hasRole(
  allowedRoles: UserRole[],
  role = getCurrentRole(),
) {
  return Boolean(role && allowedRoles.includes(role));
}

export function can(permission: Permission, role = getCurrentRole()) {
  return Boolean(role && rolePermissions[role]?.includes(permission));
}
