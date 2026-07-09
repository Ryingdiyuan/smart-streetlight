import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import AppFrame from "@/components/AppFrame.vue";
import AgentPage from "@/pages/AgentPage.vue";
import AlarmsPage from "@/pages/AlarmsPage.vue";
import DeviceDetailPage from "@/pages/DeviceDetailPage.vue";
import DevicesPage from "@/pages/DevicesPage.vue";
import HomePage from "@/pages/HomePage.vue";
import LoginPage from "@/pages/LoginPage.vue";
import MapPage from "@/pages/MapPage.vue";
import NotFoundPage from "@/pages/NotFoundPage.vue";
import ProfilePage from "@/pages/ProfilePage.vue";
import { getAuthSession } from "@/services/authStorage";
import { can } from "@/services/permissions";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: AppFrame,
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "home", component: HomePage, meta: { title: "移动首页" } },
      { path: "devices", name: "devices", component: DevicesPage, meta: { title: "设备列表" } },
      { path: "devices/:id", name: "device-detail", component: DeviceDetailPage, meta: { title: "设备详情" } },
      { path: "map", name: "map", component: MapPage, meta: { title: "设备地图", permission: "viewDevices" } },
      { path: "alarms", name: "alarms", component: AlarmsPage, meta: { title: "告警中心", permission: "handleAlarms" } },
      { path: "agent", name: "agent", component: AgentPage, meta: { title: "智能问答", permission: "viewAgent" } },
      { path: "profile", name: "profile", component: ProfilePage, meta: { title: "我的" } },
    ],
  },
  { path: "/login", name: "login", component: LoginPage, meta: { title: "登录" } },
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundPage, meta: { title: "页面不存在" } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const hasSession = Boolean(getAuthSession());

  if (to.name === "login" && hasSession) {
    return "/";
  }

  if (requiresAuth && !hasSession) {
    return {
      name: "login",
      query: { redirect: to.fullPath },
    };
  }

  const permission = to.meta.permission as Parameters<typeof can>[0] | undefined;
  if (requiresAuth && permission && !can(permission)) {
    return "/";
  }

  return true;
});

router.afterEach((to) => {
  const title = typeof to.meta.title === "string" ? to.meta.title : "智慧路灯移动端";
  document.title = `${title} | 智慧路灯移动端`;
});

export default router;
