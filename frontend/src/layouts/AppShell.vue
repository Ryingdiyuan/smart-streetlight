<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand-block">
        <p class="brand-subtitle">Smart Streetlight</p>
        <h1>智慧路灯节能系统</h1>
      </div>

      <nav class="nav-list">
        <RouterLink v-for="item in visibleNavItems" :key="item.to" :to="item.to" custom v-slot="{ navigate, href }">
          <a
            :href="href"
            class="nav-item"
            :class="{ 'nav-item-active': isNavItemActive(item.to) }"
            @click="navigate"
          >
            <span class="nav-label">{{ item.label }}</span>
            <span class="nav-desc">{{ item.description }}</span>
          </a>
        </RouterLink>
      </nav>
    </aside>

    <div class="app-main">
      <header class="topbar">
        <div>
          <p class="topbar-kicker">管理端控制台</p>
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="topbar-actions">
          <div class="topbar-status">
            <span class="status-dot"></span>
            <span>当前用户：{{ currentUsername }}（{{ currentRoleLabel }}）</span>
          </div>
          <button class="theme-toggle-button" type="button" @click="toggleTheme">
            {{ theme === "dark" ? "正常模式" : "夜间模式" }}
          </button>
          <button class="ghost-button" type="button" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { clearAuthSession, getAuthSession } from "@/services/authStorage";
import { can, getRoleLabel, type Permission } from "@/services/permissions";
import { getStoredTheme, saveTheme, type AppTheme } from "@/services/themeStorage";

const route = useRoute();
const router = useRouter();
const theme = ref<AppTheme>(getStoredTheme());

interface NavItem {
  to: string;
  label: string;
  description: string;
  permission: Permission;
}

const navItems: NavItem[] = [
  { to: "/", label: "总览大屏", description: "实时概览与图表入口", permission: "viewDashboard" },
  { to: "/software-devices", label: "软件设备中心", description: "设备建档与业务入口", permission: "manageDeviceRegistry" },
  { to: "/devices", label: "设备列表", description: "设备管理与详情跳转", permission: "viewDevices" },
  { to: "/map", label: "设备地图", description: "GIS 可视化分布", permission: "viewDevices" },
  { to: "/realtime-light", label: "实时光照监测", description: "传感器实时数据", permission: "viewDevices" },
  { to: "/light-history", label: "历史光照数据", description: "光照趋势与统计", permission: "viewDevices" },
  { to: "/alarms", label: "告警日志", description: "离线和异常告警记录", permission: "viewDevices" },
  { to: "/users", label: "用户管理", description: "账号、角色与状态维护", permission: "manageUsers" },
  { to: "/agent", label: "智能问答", description: "维护建议与故障排查", permission: "viewAgent" },
];

const visibleNavItems = computed(() => navItems.filter((item) => can(item.permission)));

const currentTitle = computed(() => {
  if (typeof route.meta.title === "string") {
    return route.meta.title;
  }
  return "智慧路灯节能系统";
});

const currentUsername = computed(() => getAuthSession()?.user.username ?? "未登录");
const currentRoleLabel = computed(() => getRoleLabel(getAuthSession()?.user.role));

function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
  saveTheme(theme.value);
}

function isNavItemActive(path: string) {
  if (path === "/") return route.path === "/";
  if (path === "/devices") return route.path === "/devices" || route.path.startsWith("/devices/");
  return route.path === path;
}

async function handleLogout() {
  clearAuthSession();
  await router.push("/login");
}
</script>
