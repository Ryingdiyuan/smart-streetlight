<template>
  <view>
    <page-meta :page-style="'background-color: #07111d; color: #e8edf3;'" />
    <slot />
  </view>
</template>

<script setup lang="ts">
import { onLaunch, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/stores/auth";

onLaunch(() => {
  const auth = useAuthStore();
  auth.restoreSession();
});

onShow(() => {
  const auth = useAuthStore();
  if (!auth.token) {
    auth.restoreSession();
  }
  const pages = getCurrentPages();
  const currentRoute =
    pages.length > 0 ? pages[pages.length - 1].route : "";
  if (
    currentRoute &&
    !currentRoute.startsWith("pages/login") &&
    !auth.isLoggedIn
  ) {
    uni.reLaunch({ url: "/pages/login/index" });
  }
});
</script>

<style>
/* Global styles */
page {
  background-color: #07111d;
  color: #e8edf3;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica,
    Arial, sans-serif;
}

view {
  box-sizing: border-box;
}

text {
  box-sizing: border-box;
}
</style>
