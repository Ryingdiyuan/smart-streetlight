<template>
  <view class="login-page">
    <view class="login-card">
      <view class="login-header">
        <text class="logo">💡</text>
        <text class="title">智慧路灯节能系统</text>
        <text class="subtitle">Smart Streetlight</text>
      </view>

      <view class="form-group">
        <text class="form-label">用户名</text>
        <input
          class="form-input"
          v-model="username"
          placeholder="请输入用户名"
          placeholder-class="placeholder"
          @confirm="doLogin"
        />
      </view>

      <view class="form-group">
        <text class="form-label">密码</text>
        <input
          class="form-input"
          v-model="password"
          type="password"
          placeholder="请输入密码"
          placeholder-class="placeholder"
          @confirm="doLogin"
        />
      </view>

      <view v-if="errorMsg" class="error-msg">
        <text>{{ errorMsg }}</text>
      </view>

      <view class="login-btn" :class="{ loading: isLoading }" @tap="doLogin">
        <text v-if="!isLoading">登 录</text>
        <text v-else>登录中...</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const username = ref("admin");
const password = ref("123456");
const errorMsg = ref("");
const isLoading = ref(false);

async function doLogin() {
  if (!username.value || !password.value) {
    errorMsg.value = "请输入用户名和密码";
    return;
  }

  isLoading.value = true;
  errorMsg.value = "";

  try {
    await auth.login(username.value, password.value);
    uni.reLaunch({ url: "/pages/tabbar/dashboard/index" });
  } catch (err: unknown) {
    const e = err as { detail?: string; message?: string };
    errorMsg.value = e.detail || e.message || "登录失败，请检查用户名和密码";
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: radial-gradient(
      ellipse at 20% 50%,
      rgba(56, 213, 255, 0.08) 0%,
      transparent 50%
    ),
    radial-gradient(
      ellipse at 80% 50%,
      rgba(255, 193, 7, 0.05) 0%,
      transparent 50%
    ),
    #07111d;
}

.login-card {
  width: 100%;
  max-width: 360px;
  background: rgba(10, 26, 45, 0.9);
  border: 1px solid rgba(56, 213, 255, 0.2);
  border-radius: 16px;
  padding: 32px 24px;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
  gap: 8px;
}

.logo {
  font-size: 48px;
}

.title {
  font-size: 20px;
  font-weight: 700;
  color: #e8edf3;
}

.subtitle {
  font-size: 12px;
  color: #6a8299;
  letter-spacing: 1px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  font-size: 14px;
  color: #9fb4c8;
  margin-bottom: 8px;
  display: block;
}

.form-input {
  width: 100%;
  height: 46px;
  background: rgba(7, 17, 29, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.2);
  border-radius: 10px;
  padding: 0 14px;
  color: #e8edf3;
  font-size: 16px;
}

.error-msg {
  background: rgba(255, 82, 82, 0.1);
  border: 1px solid rgba(255, 82, 82, 0.3);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 16px;
}

.error-msg text {
  color: #ff5252;
  font-size: 13px;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #38d5ff, #1a8bb8);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 8px;
}

.login-btn text {
  color: #07111d;
  font-size: 17px;
  font-weight: 600;
}

.login-btn.loading {
  opacity: 0.7;
}
</style>
