<template>
  <div class="mobile-shell">
    <header class="mobile-header">
      <div>
        <p class="mobile-kicker">移动运维端</p>
        <h1>{{ title }}</h1>
      </div>
      <button class="theme-chip" type="button" @click="toggleTheme">
        {{ theme === "aurora-night" ? "浅色" : "深色" }}
      </button>
    </header>

    <main class="mobile-main">
      <RouterView />
    </main>

    <nav class="bottom-nav">
      <RouterLink
        v-for="item in visibleItems"
        :key="item.to"
        :to="item.to"
        class="bottom-nav-item"
        :class="{ 'bottom-nav-item-active': isItemActive(item.to) }"
      >
        <component :is="item.icon" :size="18" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import { Bell, Bot, LayoutGrid, MapPinned, Smartphone, UserRound } from "lucide-vue-next";
import { can } from "@/services/permissions";
import { getStoredTheme, saveTheme, type AppTheme } from "@/services/themeStorage";

const route = useRoute();
const theme = ref<AppTheme>(getStoredTheme());

const navItems = [
  { to: "/", label: "首页", icon: LayoutGrid, permission: "viewDashboard" as const, title: "移动首页" },
  { to: "/devices", label: "设备", icon: Smartphone, permission: "viewDevices" as const, title: "设备列表" },
  { to: "/map", label: "地图", icon: MapPinned, permission: "viewDevices" as const, title: "设备地图" },
  { to: "/alarms", label: "告警", icon: Bell, permission: "handleAlarms" as const, title: "告警中心" },
  { to: "/agent", label: "AI", icon: Bot, permission: "viewAgent" as const, title: "智能问答" },
  { to: "/profile", label: "我的", icon: UserRound, permission: "viewDashboard" as const, title: "我的" },
];

const visibleItems = computed(() => navItems.filter((item) => can(item.permission)));
const title = computed(() => {
  if (typeof route.meta.title === "string") {
    return route.meta.title;
  }
  return navItems.find((item) => item.to === route.path)?.title ?? "移动运维端";
});

function isItemActive(path: string) {
  if (path === "/") {
    return route.path === "/";
  }
  if (path === "/devices") {
    return route.path === "/devices" || route.path.startsWith("/devices/");
  }
  return route.path === path;
}

function toggleTheme() {
  theme.value = theme.value === "aurora-night" ? "mist-light" : "aurora-night";
  saveTheme(theme.value);
}
</script>

<style scoped>
.mobile-shell {
  min-height: 100vh;
  padding: calc(env(safe-area-inset-top, 0px) + 16px) 16px calc(env(safe-area-inset-bottom, 0px) + 92px);
}

.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.mobile-kicker {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.mobile-header h1 {
  margin: 0;
  font-size: 22px;
}

.mobile-main {
  display: grid;
  gap: 16px;
}

.bottom-nav {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: calc(env(safe-area-inset-bottom, 0px) + 12px);
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
  padding: 10px;
  border-radius: 24px;
  border: 1px solid var(--border-strong);
  background: var(--surface-nav);
  backdrop-filter: blur(16px);
  box-shadow: var(--overlay-shadow);
}

.bottom-nav-item {
  display: grid;
  justify-items: center;
  gap: 4px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 10px;
  padding: 8px 2px;
  border-radius: 16px;
}

.bottom-nav-item-active {
  color: var(--text-primary);
  background: linear-gradient(180deg, var(--chip-active-bg), transparent);
}

@media (min-width: 768px) {
  .mobile-shell {
    max-width: 520px;
    margin: 0 auto;
  }
}
</style>
