import { http } from "@/lib/http";
import type { AgentMessage, AgentPromptOption, AgentQuestionOptions } from "@/types/models";

interface AgentChatResponse {
  answer?: string;
  content?: string;
  source?: string;
  related_device?: {
    id: number;
    device_code: string;
    device_name: string;
  } | null;
}

interface ChatHistoryResponse {
  messages: Array<{
    id: number;
    user_id: number;
    role: string;
    content: string;
    device_id: number | null;
    device_code: string | null;
    created_at: string;
  }>;
  total: number;
}

const builtinPrompts: AgentPromptOption[] = [
  { id: "api-p1", title: "SL-001 离线后应该怎么排查？" },
  { id: "api-p2", title: "控制命令发送成功但设备未响应怎么办？" },
  { id: "api-p3", title: "阈值应该如何设置更合理？" },
];

export async function getPromptOptions(): Promise<AgentPromptOption[]> {
  return builtinPrompts;
}

export async function getConversation(): Promise<AgentMessage[]> {
  const response = await http.get<ChatHistoryResponse>("/agent/history");
  return response.messages.map((msg) => ({
    id: `${msg.role}-${msg.id}`,
    role: msg.role as "user" | "assistant",
    content: msg.content,
  }));
}

export async function sendQuestion(
  question: string,
  options: AgentQuestionOptions = {},
): Promise<AgentMessage> {
  const response = await http.post<AgentChatResponse>("/agent/chat", {
    question,
    ...(options.deviceId ? { device_id: options.deviceId } : {}),
    ...(options.deviceCode ? { device_code: options.deviceCode } : {}),
  });

  const scopeHint = response.related_device
    ? `\n\n提问范围：${response.related_device.device_code} ${response.related_device.device_name}`
    : "";

  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content:
      (response.answer ?? response.content ?? "接口已返回，但当前没有可展示的回答内容。") +
      scopeHint,
  };
}

export async function clearHistory(): Promise<void> {
  await http.delete("/agent/history");
}
