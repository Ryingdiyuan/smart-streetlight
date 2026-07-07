import { createRouter, createWebHistory } from "vue-router";

import AppShell from "@/layouts/AppShell.vue";
import ForbiddenPage from "@/pages/ForbiddenPage.vue";
import HardwareDashboardPage from "@/pages/HardwareDashboardPage.vue";
import LoginPage from "@/pages/LoginPage.vue";
import NotFoundPage from "@/pages/NotFoundPage.vue";
import SimulatorConsolePage from "@/pages/SimulatorConsolePage.vue";
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
        {
          path: "",
          name: "hardware-dashboard",
          component: HardwareDashboardPage,
          meta: { title: "硬件联调首页", roles: allRoles },
        },
        {
          path: "simulator",
          name: "simulator",
          component: SimulatorConsolePage,
          meta: { title: "硬件联调控制台", roles: adminOnly },
        },
        {
          path: "forbidden",
          name: "forbidden",
          component: ForbiddenPage,
          meta: { title: "无权限访问", roles: allRoles },
        },
      ],
    },
    {
      path: "/login",
      name: "login",
      component: LoginPage,
      meta: { title: "登录" },
    },
    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: NotFoundPage,
      meta: { title: "页面不存在" },
    },
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
  const pageTitle = typeof to.meta.title === "string" ? to.meta.title : "智慧路灯硬件联调前端";
  document.title = `${pageTitle} | 智慧路灯硬件联调前端`;
});

export default router;
