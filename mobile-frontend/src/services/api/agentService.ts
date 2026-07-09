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

const builtinPrompts: AgentPromptOption[] = [
  { id: "m-agent-1", title: "哪些设备需要优先关注？" },
  { id: "m-agent-2", title: "SL-001 离线后应该怎么排查？" },
  { id: "m-agent-3", title: "阈值怎样设置更合理？" },
];

export function getPromptOptions() {
  return Promise.resolve(builtinPrompts);
}

export async function sendQuestion(question: string, options: AgentQuestionOptions = {}): Promise<AgentMessage> {
  const response = await http.post<AgentChatResponse>("/agent/chat", {
    question,
    ...(options.deviceId ? { device_id: options.deviceId } : {}),
    ...(options.deviceCode ? { device_code: options.deviceCode } : {}),
  });

  const scopeHint = response.related_device
    ? `\n\n提问范围：${response.related_device.device_code} ${response.related_device.device_name}`
    : "";
  const sourceHint =
    response.source === "fallback"
      ? "\n\n当前模式：规则版兜底回答"
      : response.source === "mock"
        ? "\n\n当前模式：规则版回答"
        : "";

  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: `${response.answer ?? response.content ?? "当前没有可展示的回答内容。"}${scopeHint}${sourceHint}`,
  };
}
