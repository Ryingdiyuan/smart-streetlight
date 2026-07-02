<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand-block">
        <p class="brand-subtitle">Smart Streetlight</p>
        <h1>智慧路灯节能系统</h1>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class="nav-item-active"
        >
          <span class="nav-label">{{ item.label }}</span>
          <span class="nav-desc">{{ item.description }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="app-main">
      <header class="topbar">
        <div>
          <p class="topbar-kicker">管理端骨架</p>
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="topbar-status">
          <span class="status-dot"></span>
          <span>后续可接入实时数据刷新</span>
        </div>
      </header>

      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const navItems = [
  { to: "/", label: "总览大屏", description: "实时概览与图表入口" },
  { to: "/devices", label: "设备列表", description: "设备管理与详情跳转" },
  { to: "/alarms", label: "告警日志", description: "离线和异常告警记录" },
  { to: "/agent", label: "智能问答", description: "维护建议与故障排查" },
];

const currentTitle = computed(() => {
  if (typeof route.meta.title === "string") {
    return route.meta.title;
  }
  return "智慧路灯节能系统";
});
</script>
