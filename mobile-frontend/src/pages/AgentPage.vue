<template>
  <div class="page-stack">
    <SectionCard title="快捷问题" subtitle="适配现场演示和运维排查">
      <div class="chip-row">
        <button v-for="prompt in prompts" :key="prompt.id" class="chip-button" type="button" @click="question = prompt.title">
          {{ prompt.title }}
        </button>
      </div>
    </SectionCard>

    <SectionCard title="智能问答" subtitle="支持系统级和指定设备提问">
      <select v-model="selectedDeviceCode">
        <option value="">系统整体</option>
        <option v-for="device in devices" :key="device.id" :value="device.deviceCode">
          {{ device.deviceCode }} - {{ device.deviceName }}
        </option>
      </select>

      <div class="chat-list">
        <article
          v-for="message in messages"
          :key="message.id"
          class="chat-bubble"
          :class="message.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'"
        >
          {{ message.content }}
        </article>
      </div>

      <textarea
        v-model="question"
        rows="4"
        placeholder="例如：SL-001 离线后应该怎么排查？"
      ></textarea>

      <button class="action-button" type="button" :disabled="submitting" @click="submitQuestion">
        {{ submitting ? "发送中..." : "发送问题" }}
      </button>
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import SectionCard from "@/components/SectionCard.vue";
import { getPromptOptions, sendQuestion } from "@/services/api/agentService";
import { getDeviceList } from "@/services/api/deviceService";
import type { AgentMessage, AgentPromptOption, Device } from "@/types/models";

const prompts = ref<AgentPromptOption[]>([]);
const devices = ref<Device[]>([]);
const messages = ref<AgentMessage[]>([]);
const question = ref("");
const selectedDeviceCode = ref("");
const submitting = ref(false);

const selectedDevice = computed(() =>
  devices.value.find((device) => device.deviceCode === selectedDeviceCode.value) ?? null,
);

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return "请求失败，请稍后重试。";
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message;
  }
}

async function submitQuestion() {
  const currentQuestion = question.value.trim();
  if (!currentQuestion || submitting.value) {
    return;
  }

  messages.value.push({
    id: `user-${Date.now()}`,
    role: "user",
    content: currentQuestion,
  });

  submitting.value = true;
  try {
    const answer = await sendQuestion(currentQuestion, {
      deviceId: selectedDevice.value?.id,
      deviceCode: selectedDevice.value?.deviceCode,
    });
    messages.value.push(answer);
    question.value = "";
  } catch (error) {
    messages.value.push({
      id: `assistant-error-${Date.now()}`,
      role: "assistant",
      content: `请求失败：${getErrorMessage(error)}`,
    });
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  prompts.value = await getPromptOptions();
  devices.value = await getDeviceList().catch(() => []);
});
</script>

<style scoped>
.chat-list {
  display: grid;
  gap: 10px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.chat-bubble {
  padding: 12px 14px;
  border-radius: 18px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.chat-bubble-user {
  background: rgba(54, 215, 255, 0.14);
  border: 1px solid rgba(54, 215, 255, 0.22);
}

.chat-bubble-assistant {
  background: var(--surface-inner);
  border: 1px solid var(--border-soft);
}
</style>
