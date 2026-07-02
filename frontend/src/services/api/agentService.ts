import { http } from "@/lib/http";
import type { AgentMessage, AgentPromptOption } from "@/types/models";

interface AgentChatResponse {
  answer?: string;
  content?: string;
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
  return [];
}

export async function sendQuestion(question: string): Promise<AgentMessage> {
  const response = await http.post<AgentChatResponse>("/agent/chat", { question });
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: response.answer ?? response.content ?? "接口已返回，但当前没有可展示的回答内容。",
  };
}
