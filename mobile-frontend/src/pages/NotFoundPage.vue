<template>
  <section class="page-stack">
    <SectionCard title="页面不存在" subtitle="该页面可能已移动或路径输入错误">
      <p class="placeholder-text">请返回首页或重新选择底部导航。</p>
      <RouterLink class="action-button" to="/">返回首页</RouterLink>
    </SectionCard>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import SectionCard from "@/components/SectionCard.vue";
</script>
