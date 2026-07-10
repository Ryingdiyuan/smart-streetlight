<template>
  <div v-if="isBigscreenRoute" class="bigscreen-shell">
    <div class="bigscreen-hot-zone" @mouseenter="drawerHovered = true"></div>

    <button class="bigscreen-menu-button" type="button" @click="toggleDrawerPin">
      {{ isDrawerOpen ? "收起导航" : "菜单" }}
    </button>

    <aside
      class="bigscreen-nav-drawer"
      :class="{ 'bigscreen-nav-drawer-open': isDrawerOpen }"
      @mouseenter="drawerHovered = true"
      @mouseleave="drawerHovered = false"
    >
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

      <div class="bigscreen-drawer-actions">
        <button class="theme-toggle-button" type="button" @click="toggleTheme">
          {{ theme === "dark" ? "日间模式" : "夜间模式" }}
        </button>
        <button class="ghost-button" type="button" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <main class="bigscreen-content">
      <RouterView />
    </main>
  </div>

  <div v-else class="app-shell">
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
            {{ theme === "dark" ? "日间模式" : "夜间模式" }}
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
const drawerHovered = ref(false);
const drawerPinned = ref(false);

interface NavItem {
  to: string;
  label: string;
  description: string;
  permission: Permission;
}

const navItems: NavItem[] = [
  { to: "/", label: "总览大屏", description: "实时概览与投屏展示", permission: "viewDashboard" },
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
const isBigscreenRoute = computed(() => route.meta.bigscreen === true);
const isDrawerOpen = computed(() => drawerHovered.value || drawerPinned.value);

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

function toggleDrawerPin() {
  drawerPinned.value = !drawerPinned.value;
  drawerHovered.value = drawerPinned.value;
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

<style scoped>
.bigscreen-shell {
  position: fixed;
  inset: 0;
  overflow: hidden;
  color: #eaf7ff;
  background: #020712;
}

.bigscreen-content {
  width: 100%;
  height: 100%;
}

.bigscreen-hot-zone {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 42;
  width: 24px;
}

.bigscreen-menu-button {
  position: fixed;
  top: 18px;
  left: 18px;
  z-index: 50;
  min-width: 64px;
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(91, 214, 255, 0.38);
  border-radius: 4px;
  color: #d8f7ff;
  background: rgba(4, 18, 35, 0.72);
  box-shadow: 0 0 18px rgba(46, 197, 255, 0.18);
}

.bigscreen-nav-drawer {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 48;
  width: 292px;
  padding: 76px 20px 22px;
  overflow-y: auto;
  border-right: 1px solid rgba(91, 214, 255, 0.28);
  background:
    linear-gradient(180deg, rgba(2, 9, 19, 0.98), rgba(4, 22, 42, 0.96)),
    radial-gradient(circle at 42% 8%, rgba(60, 205, 255, 0.18), transparent 38%);
  box-shadow: 18px 0 48px rgba(0, 0, 0, 0.5), 0 0 34px rgba(46, 197, 255, 0.12);
  transform: translateX(-104%);
  transition: transform 0.24s ease;
}

.bigscreen-nav-drawer-open {
  transform: translateX(0);
}

.bigscreen-drawer-actions {
  display: grid;
  gap: 12px;
  margin-top: 22px;
}

@media (max-width: 720px) {
  .bigscreen-shell {
    position: relative;
    min-height: 100vh;
    overflow: auto;
  }

  .bigscreen-content {
    min-height: 100vh;
    height: auto;
  }
}
</style>
