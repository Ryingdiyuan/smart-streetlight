import { createRouter, createWebHistory } from "vue-router";

import AppShell from "@/layouts/AppShell.vue";
import AgentPage from "@/pages/AgentPage.vue";
import AlarmPage from "@/pages/AlarmPage.vue";
import DashboardPage from "@/pages/DashboardPage.vue";
import DeviceDetailPage from "@/pages/DeviceDetailPage.vue";
import DeviceListPage from "@/pages/DeviceListPage.vue";
import LightHistoryPage from "@/pages/LightHistoryPage.vue";
import LoginPage from "@/pages/LoginPage.vue";
import NotFoundPage from "@/pages/NotFoundPage.vue";
import RealtimeLightPage from "@/pages/RealtimeLightPage.vue";
import SimulatorConsolePage from "@/pages/SimulatorConsolePage.vue";
import { getAccessToken } from "@/services/authStorage";

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
          name: "dashboard",
          component: DashboardPage,
          meta: { title: "总览大屏" },
        },
        {
          path: "devices",
          name: "devices",
          component: DeviceListPage,
          meta: { title: "设备列表" },
        },
        {
          path: "devices/:id",
          name: "device-detail",
          component: DeviceDetailPage,
          meta: { title: "设备详情" },
        },
        {
          path: "alarms",
          name: "alarms",
          component: AlarmPage,
          meta: { title: "告警日志" },
        },
        {
          path: "agent",
          name: "agent",
          component: AgentPage,
          meta: { title: "智能问答" },
        },
        {
          path: "realtime-light",
          name: "realtime-light",
          component: RealtimeLightPage,
          meta: { title: "实时光照监测" },
        },
        {
          path: "light-history",
          name: "light-history",
          component: LightHistoryPage,
          meta: { title: "历史光照数据" },
        },
        {
          path: "simulator",
          name: "simulator",
          component: SimulatorConsolePage,
          meta: { title: "模拟器控制台" },
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
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

  if (to.name === "login" && hasToken) {
    return { name: "dashboard" };
  }

  if (requiresAuth && !hasToken) {
    return {
      name: "login",
      query: typeof to.fullPath === "string" && to.fullPath !== "/login" ? { redirect: to.fullPath } : {},
    };
  }

  return true;
});

router.afterEach((to) => {
  const pageTitle =
    typeof to.meta.title === "string" ? to.meta.title : "智慧路灯节能系统";
  document.title = `${pageTitle} | 智慧路灯节能系统`;
});

export default router;
