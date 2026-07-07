<template>
  <section class="login-page">
    <div class="login-card card">
      <div class="login-header">
        <p class="section-kicker">Auth</p>
        <h2>登录系统</h2>
        <p class="login-note">先完成最小登录链路，后续再补路由守卫和角色权限控制。</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <label>
          <span>用户名</span>
          <input
            v-model.trim="form.username"
            class="search-input"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </label>

        <label>
          <span>密码</span>
          <input
            v-model="form.password"
            class="search-input"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </label>

        <p v-if="errorMessage" class="login-error">{{ errorMessage }}</p>

        <button class="primary-button login-button" type="submit" :disabled="submitting">
          {{ submitting ? "登录中..." : "登录" }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { login } from "@/services/api/authService";
import { saveAuthSession } from "@/services/authStorage";

const route = useRoute();
const router = useRouter();

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

  // HttpError already contains the backend detail message
  if ("detail" in error && typeof (error as { detail: string }).detail === "string") {
    return (error as { detail: string }).detail;
  }

  return error.message || "登录失败，请稍后重试。";
}

async function handleSubmit() {
  if (!form.username || !form.password) {
    errorMessage.value = "请输入用户名和密码。";
    return;
  }

  submitting.value = true;
  errorMessage.value = "";

  try {
    const result = await login({
      username: form.username,
      password: form.password,
    });

    saveAuthSession({
      token: result.access_token,
      user: result.user,
    });

    const redirectTarget =
      typeof route.query.redirect === "string" && route.query.redirect.startsWith("/")
        ? route.query.redirect
        : "/";

    await router.push(redirectTarget);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
}

.login-card {
  width: min(100%, 420px);
  padding: 28px;
}

.login-header {
  display: grid;
  gap: 8px;
  margin-bottom: 24px;
}

.login-header h2,
.login-note {
  margin: 0;
}

.login-note {
  color: #94a3b8;
}

.login-form {
  display: grid;
  gap: 16px;
}

.login-form label {
  display: grid;
  gap: 8px;
}

.login-error {
  margin: 0;
  color: #fca5a5;
}

.login-button {
  width: 100%;
}

.login-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}
</style>
