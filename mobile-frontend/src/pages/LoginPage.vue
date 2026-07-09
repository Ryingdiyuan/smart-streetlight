<template>
  <section class="login-page">
    <div class="login-brand">
      <p>Smart Streetlight</p>
      <h1>移动运维端</h1>
      <span>让值班、巡检、告警处理与远程控制都能在手机上完成。</span>
    </div>

    <form class="login-card" @submit.prevent="handleSubmit">
      <div class="input-group">
        <label for="username">用户名</label>
        <input id="username" v-model.trim="form.username" type="text" placeholder="请输入用户名" />
      </div>

      <div class="input-group">
        <label for="password">密码</label>
        <input id="password" v-model="form.password" type="password" placeholder="请输入密码" />
      </div>

      <p class="login-tip">演示账号默认可使用 `admin / 123456`。</p>
      <p v-if="errorMessage" class="login-error">{{ errorMessage }}</p>

      <button class="action-button login-button" type="submit" :disabled="submitting">
        {{ submitting ? "登录中..." : "进入移动运维端" }}
      </button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "admin",
  password: "123456",
});

const submitting = ref(false);
const errorMessage = ref("");

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "登录失败，请稍后重试。";
  }

  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message || "登录失败，请稍后重试。";
  }
}

async function handleSubmit() {
  if (!form.username || !form.password) {
    errorMessage.value = "请输入用户名和密码。";
    return;
  }

  submitting.value = true;
  errorMessage.value = "";
  try {
    await authStore.login(form);
    const redirectTarget =
      typeof route.query.redirect === "string" && route.query.redirect.startsWith("/")
        ? route.query.redirect
        : "/";
    await router.replace(redirectTarget);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: calc(env(safe-area-inset-top, 0px) + 28px) 18px 28px;
  display: grid;
  align-content: center;
  gap: 22px;
  background:
    radial-gradient(circle at top, rgba(54, 215, 255, 0.22), transparent 34%),
    linear-gradient(180deg, #07111d 0%, #091520 52%, #050b14 100%);
}

.login-brand {
  display: grid;
  gap: 8px;
}

.login-brand p,
.login-brand h1,
.login-brand span {
  margin: 0;
}

.login-brand p {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
}

.login-brand h1 {
  font-size: 36px;
}

.login-brand span {
  color: var(--text-secondary);
  line-height: 1.7;
}

.login-card {
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(89, 120, 176, 0.24);
  background: rgba(9, 18, 31, 0.88);
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.input-group {
  display: grid;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  color: var(--text-secondary);
}

.login-tip {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}

.login-error {
  margin: 0;
  color: #ff9b9b;
  font-size: 13px;
}

.login-button {
  min-height: 50px;
  font-size: 15px;
}
</style>
