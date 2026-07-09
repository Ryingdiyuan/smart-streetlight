<template>
  <view class="agent-page">
    <!-- Quick prompts -->
    <scroll-view class="prompts-row" scroll-x v-if="prompts.length > 0">
      <view
        v-for="prompt in prompts"
        :key="prompt.id"
        class="prompt-chip"
        @tap="sendPrompt(prompt.title)"
      >
        <text>{{ prompt.title }}</text>
      </view>
      <view class="prompt-chip clear-chip" @tap="handleClear">
        <text>清空对话</text>
      </view>
    </scroll-view>

    <!-- Chat messages -->
    <scroll-view
      class="chat-scroll"
      scroll-y
      :scroll-into-view="scrollToId"
      scroll-with-animation
    >
      <view v-if="messages.length === 0 && !thinking" class="welcome-msg">
        <text class="welcome-icon">💡</text>
        <text class="welcome-text">你好！我是智能运维助手，\n可以回答设备相关问题。</text>
      </view>

      <view
        v-for="(msg, index) in messages"
        :key="msg.id"
        :id="'msg-' + index"
        class="message-row"
        :class="msg.role"
      >
        <view class="message-bubble" :class="msg.role">
          <text class="message-content">{{ msg.content }}</text>
        </view>
      </view>

      <!-- Thinking indicator -->
      <view v-if="thinking" class="message-row assistant" id="thinking-indicator">
        <view class="message-bubble assistant thinking">
          <text class="thinking-dots">思考中</text>
          <text class="dot">.</text>
          <text class="dot">.</text>
          <text class="dot">.</text>
        </view>
      </view>
    </scroll-view>

    <!-- Input area -->
    <view class="input-area">
      <input
        class="msg-input"
        v-model="question"
        placeholder="输入您的问题..."
        placeholder-class="placeholder"
        @confirm="sendMessage"
        :disabled="thinking"
      />
      <view class="send-btn" :class="{ disabled: !question.trim() || thinking }" @tap="sendMessage">
        <text>发送</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { onShow } from "@dcloudio/uni-app";
import type { AgentMessage, AgentPromptOption } from "@/types/models";
import {
  sendQuestion,
  getConversation,
  clearHistory,
  getPromptOptions,
} from "@/services/api/agentService";

const messages = ref<AgentMessage[]>([]);
const question = ref("");
const thinking = ref(false);
const prompts = ref<AgentPromptOption[]>([]);
const scrollToId = ref("");

async function loadHistory() {
  try {
    messages.value = await getConversation();
  } catch (err) {
    console.error("加载对话历史失败", err);
  }
}

async function handleClear() {
  uni.showModal({
    title: "确认清空",
    content: "确定要清空所有对话记录吗？",
    success: async (res) => {
      if (res.confirm) {
        try {
          await clearHistory();
          messages.value = [];
          uni.showToast({ title: "已清空", icon: "success" });
        } catch (err) {
          uni.showToast({ title: "清空失败", icon: "error" });
        }
      }
    },
  });
}

async function sendMessage() {
  const text = question.value.trim();
  if (!text || thinking.value) return;

  // Add user message
  const userMsg: AgentMessage = {
    id: `user-${Date.now()}`,
    role: "user",
    content: text,
  };
  messages.value.push(userMsg);
  question.value = "";
  thinking.value = true;
  scrollToBottom();

  try {
    const reply = await sendQuestion(text);
    messages.value.push(reply);
  } catch (err) {
    messages.value.push({
      id: `err-${Date.now()}`,
      role: "assistant",
      content: "抱歉，我暂时无法回答这个问题，请稍后重试。",
    });
  } finally {
    thinking.value = false;
    scrollToBottom();
  }
}

function sendPrompt(title: string) {
  question.value = title;
  sendMessage();
}

function scrollToBottom() {
  nextTick(() => {
    scrollToId.value = `msg-${messages.value.length - 1}`;
  });
}

onShow(() => {
  loadHistory();
  getPromptOptions().then((p) => {
    prompts.value = p;
  });

  // Add clear button to nav bar
  uni.setNavigationBarTitle({
    title: "智能问答",
  });
});
</script>

<style scoped>
.agent-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 12px;
}

.prompts-row {
  display: flex;
  white-space: nowrap;
  padding: 10px 0;
  margin-bottom: 4px;
}

.prompt-chip {
  display: inline-flex;
  padding: 6px 14px;
  border-radius: 16px;
  background: rgba(56, 213, 255, 0.1);
  border: 1px solid rgba(56, 213, 255, 0.2);
  margin-right: 8px;
  font-size: 12px;
  color: #38d5ff;
  flex-shrink: 0;
}

.clear-chip {
  background: rgba(255, 82, 82, 0.1);
  border-color: rgba(255, 82, 82, 0.3);
  color: #ff5252;
}

.chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.welcome-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  gap: 12px;
}

.welcome-icon {
  font-size: 48px;
}

.welcome-text {
  font-size: 14px;
  color: #6a8299;
  text-align: center;
  white-space: pre-line;
}

.message-row {
  margin-bottom: 12px;
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
}

.message-bubble.user {
  background: rgba(56, 213, 255, 0.2);
  border: 1px solid rgba(56, 213, 255, 0.3);
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(158, 180, 200, 0.2);
  border-bottom-left-radius: 4px;
}

.message-content {
  font-size: 14px;
  color: #e8edf3;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking {
  display: flex;
  align-items: center;
  gap: 2px;
}

.thinking-dots {
  font-size: 14px;
  color: #9fb4c8;
}

.dot {
  animation: blink 1.4s infinite;
  font-size: 14px;
  color: #9fb4c8;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}
.dot:nth-child(3) {
  animation-delay: 0.4s;
}
.dot:nth-child(4) {
  animation-delay: 0.6s;
}

@keyframes blink {
  0%,
  20% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid rgba(56, 213, 255, 0.1);
}

.msg-input {
  flex: 1;
  height: 44px;
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.15);
  border-radius: 22px;
  padding: 0 16px;
  color: #e8edf3;
  font-size: 14px;
}

.send-btn {
  width: 64px;
  height: 44px;
  background: linear-gradient(135deg, #38d5ff, #1a8bb8);
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn text {
  color: #07111d;
  font-size: 14px;
  font-weight: 600;
}

.send-btn.disabled {
  opacity: 0.4;
}
</style>
