<template>
  <div class="page-stack">
    <SectionCard title="账号信息" subtitle="当前登录用户与权限说明">
      <div class="profile-card">
        <strong>{{ authStore.currentUser?.username ?? "未登录" }}</strong>
        <span>{{ getRoleLabel(authStore.currentUser?.role ?? null) }}</span>
        <p>当前移动端已接入真实后端接口，可直接查看设备、告警、地图与智能问答。</p>
      </div>
    </SectionCard>

    <SectionCard title="环境信息">
      <div class="profile-list">
        <div>
          <span>接口模式</span>
          <strong>API 直连代理</strong>
        </div>
        <div>
          <span>移动端版本</span>
          <strong>v0.1.0</strong>
        </div>
      </div>
    </SectionCard>

    <button class="action-button action-button-soft" type="button" @click="logout">退出登录</button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import SectionCard from "@/components/SectionCard.vue";
import { getRoleLabel } from "@/services/permissions";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

async function logout() {
  authStore.logout();
  await router.replace("/login");
}
</script>

<style scoped>
.profile-card,
.profile-list,
.profile-list div {
  display: grid;
  gap: 10px;
}

.profile-card strong {
  font-size: 24px;
}

.profile-card span,
.profile-list span {
  color: var(--text-secondary);
}

.profile-card p,
.profile-list strong {
  margin: 0;
}

.profile-list div {
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-inner);
  border: 1px solid var(--border-soft);
}
</style>
