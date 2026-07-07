<template>
  <span class="status-pill" :class="badgeClass">
    {{ text }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  text: string;
  status: "online" | "offline" | "success" | "warning" | "info";
}>();

const badgeClass = computed(() => {
  switch (props.status) {
    case "online":
    case "success":
      return "is-online";
    case "warning":
      return "is-warning";
    case "info":
      return "is-info";
    default:
      return "is-offline";
  }
});
</script>
