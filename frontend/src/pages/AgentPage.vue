<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Agent</p>
        <h3>智能问答</h3>
      </div>
      <p class="section-note">当前已升级为聊天面板风格，并已接入真实智能体接口。</p>
    </header>

    <div class="content-grid two-columns">
      <PanelCard title="快捷问题" subtitle="可作为答辩演示入口">
        <div class="agent-side-panel">
          <div class="summary-box">
            <strong>问答能力</strong>
            <span>设备离线排查、控制失败分析、阈值设置建议</span>
          </div>
          <div class="summary-box">
            <strong>当前模式</strong>
            <span>真实 `/api/agent/chat` 问答接口</span>
          </div>
          <div class="summary-box simulator-filter">
            <strong>提问范围</strong>
            <select v-model="selectedDeviceCode">
              <option value="">系统整体</option>
              <option v-for="device in devices" :key="device.id" :value="device.deviceCode">
                {{ device.deviceCode }} - {{ device.deviceName }}
              </option>
            </select>
            <span>可指定设备提问；未选择时会尝试从问题中自动识别设备编码。</span>
          </div>
          <div class="prompt-chip-list">
            <button
              v-for="prompt in promptOptions"
              :key="prompt.id"
              class="prompt-chip"
              @click="usePrompt(prompt.title)"
            >
              {{ prompt.title }}
            </button>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="对话面板" subtitle="维护建议与智能答复">
        <div class="chat-shell">
          <div class="chat-header-strip">
            <div>
              <strong>智慧路灯运维助手</strong>
              <span>支持故障排查、阈值建议和联调问答</span>
            </div>
            <StatusBadge :status="isThinking ? 'warning' : 'success'" :text="isThinking ? '思考中' : '就绪'" />
          </div>

          <div class="chat-box chat-panel">
            <div
              v-for="message in messages"
              :key="message.id"
              class="chat-row"
              :class="message.role === 'user' ? 'chat-row-user' : 'chat-row-agent'"
            >
              <div class="chat-avatar" :class="message.role === 'user' ? 'chat-avatar-user' : 'chat-avatar-agent'">
                {{ message.role === "user" ? "我" : "AI" }}
              </div>
              <div
                class="chat-bubble"
                :class="message.role === 'user' ? 'user-message' : 'agent-message'"
              >
                {{ message.content }}
              </div>
            </div>

            <div v-if="isThinking" class="chat-row chat-row-agent">
              <div class="chat-avatar chat-avatar-agent">AI</div>
              <div class="chat-bubble agent-message typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <div class="chat-input-panel">
            <textarea
              v-model="question"
              class="chat-textarea"
              placeholder="输入维护问题，例如：SL-003 离线后应该如何排查？"
              @keydown.enter.exact.prevent="submitQuestion"
            />
            <div class="chat-input-actions">
              <span class="inline-note">`Enter` 发送，`Shift + Enter` 换行</span>
              <div class="toolbar-actions">
                <button class="ghost-button" @click="clearConversation">清空对话</button>
                <button class="primary-button" :disabled="isThinking" @click="submitQuestion">
                  {{ isThinking ? "发送中..." : "发送问题" }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </PanelCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { clearHistory, getConversation, getPromptOptions, sendQuestion } from "@/services/agentService";
import { getDeviceList } from "@/services/deviceService";
import type { AgentMessage, AgentPromptOption, Device } from "@/types/models";

const promptOptions = ref<AgentPromptOption[]>([]);
const messages = ref<AgentMessage[]>([]);
const question = ref("");
const isThinking = ref(false);
const devices = ref<Device[]>([]);
const selectedDeviceCode = ref("");

const selectedDevice = computed(() =>
  devices.value.find((device) => device.deviceCode === selectedDeviceCode.value) ?? null,
);

function usePrompt(prompt: string) {
  question.value = prompt;
}

async function clearConversation() {
  if (messages.value.length === 0) return;
  if (!window.confirm("确定清空所有对话记录？此操作不可恢复。")) return;
  await clearHistory();
  messages.value = [];
}

function detectDeviceFromQuestion(currentQuestion: string) {
  const normalizedQuestion = currentQuestion.toUpperCase();
  return (
    devices.value.find((device) => normalizedQuestion.includes(device.deviceCode.toUpperCase())) ?? null
  );
}

async function submitQuestion() {
  const currentQuestion = question.value.trim();
  if (!currentQuestion || isThinking.value) {
    return;
  }

  const inferredDevice = selectedDevice.value ?? detectDeviceFromQuestion(currentQuestion);

  messages.value.push({
    id: `user-${Date.now()}`,
    role: "user",
    content: inferredDevice
      ? `${currentQuestion}\n\n提问范围：${inferredDevice.deviceCode} ${inferredDevice.deviceName}`
      : currentQuestion,
  });

  isThinking.value = true;
  const answer = await sendQuestion(currentQuestion, {
    deviceId: inferredDevice?.id,
    deviceCode: inferredDevice?.deviceCode,
  });
  messages.value.push(answer);
  isThinking.value = false;
  question.value = "";
}

onMounted(async () => {
  const [prompts, conversation, deviceList] = await Promise.all([
    getPromptOptions(),
    getConversation(),
    getDeviceList().catch(() => []),
  ]);
  promptOptions.value = prompts;
  messages.value = conversation;
  devices.value = deviceList;
});
</script>
