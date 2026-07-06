import { createRouter, createWebHistory } from "vue-router";

import AppShell from "@/layouts/AppShell.vue";
import AgentPage from "@/pages/AgentPage.vue";
import AlarmPage from "@/pages/AlarmPage.vue";
import DashboardPage from "@/pages/DashboardPage.vue";
import DeviceDetailPage from "@/pages/DeviceDetailPage.vue";
import DeviceListPage from "@/pages/DeviceListPage.vue";
import ForbiddenPage from "@/pages/ForbiddenPage.vue";
import LightHistoryPage from "@/pages/LightHistoryPage.vue";
import LoginPage from "@/pages/LoginPage.vue";
import NotFoundPage from "@/pages/NotFoundPage.vue";
import RealtimeLightPage from "@/pages/RealtimeLightPage.vue";
import SimulatorConsolePage from "@/pages/SimulatorConsolePage.vue";
import UserManagementPage from "@/pages/UserManagementPage.vue";
import { getAccessToken, getAuthSession } from "@/services/authStorage";
import { allRoles, getDefaultRouteForRole, hasRole } from "@/services/permissions";
import type { UserRole } from "@/types/models";

const adminOnly: UserRole[] = ["admin"];

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: AppShell,
      meta: { requiresAuth: true },
      children: [
        { path: "", name: "dashboard", component: DashboardPage, meta: { title: "总览大屏", roles: allRoles } },
        { path: "devices", name: "devices", component: DeviceListPage, meta: { title: "设备列表", roles: allRoles } },
        { path: "devices/:id", name: "device-detail", component: DeviceDetailPage, meta: { title: "设备详情", roles: allRoles } },
        { path: "alarms", name: "alarms", component: AlarmPage, meta: { title: "告警日志", roles: allRoles } },
        { path: "agent", name: "agent", component: AgentPage, meta: { title: "智能问答", roles: allRoles } },
        { path: "realtime-light", name: "realtime-light", component: RealtimeLightPage, meta: { title: "实时光照监测", roles: allRoles } },
        { path: "light-history", name: "light-history", component: LightHistoryPage, meta: { title: "历史光照数据", roles: allRoles } },
        { path: "simulator", name: "simulator", component: SimulatorConsolePage, meta: { title: "模拟器控制台", roles: adminOnly } },
        { path: "users", name: "users", component: UserManagementPage, meta: { title: "用户管理", roles: adminOnly } },
        { path: "forbidden", name: "forbidden", component: ForbiddenPage, meta: { title: "无权限访问", roles: allRoles } },
      ],
    },
    { path: "/login", name: "login", component: LoginPage, meta: { title: "登录" } },
    { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundPage, meta: { title: "页面不存在" } },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const hasToken = Boolean(getAccessToken());
  const currentRole = getAuthSession()?.user.role ?? null;
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

  if (to.name === "login" && hasToken) {
    return getDefaultRouteForRole(currentRole);
  }

  if (requiresAuth && !hasToken) {
    return {
      name: "login",
      query: typeof to.fullPath === "string" && to.fullPath !== "/login" ? { redirect: to.fullPath } : {},
    };
  }

  const allowedRoles = to.matched
    .map((record) => record.meta.roles)
    .find((roles): roles is UserRole[] => Array.isArray(roles));

  if (requiresAuth && to.name !== "forbidden" && allowedRoles && !hasRole(allowedRoles, currentRole)) {
    return { name: "forbidden" };
  }

  return true;
});

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === "string" ? to.meta.title : "智慧路灯节能系统";
  document.title = `${pageTitle} | 智慧路灯节能系统`;
});

export default router;
