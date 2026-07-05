import { mockAgentMessages, mockPromptOptions } from "@/mock/data";
import type { AgentMessage, AgentPromptOption, AgentQuestionOptions } from "@/types/models";

function delay(ms = 220) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export async function getPromptOptions(): Promise<AgentPromptOption[]> {
  await delay();
  return structuredClone(mockPromptOptions);
}

export async function getConversation(): Promise<AgentMessage[]> {
  await delay();
  return structuredClone(mockAgentMessages);
}

export async function sendQuestion(
  question: string,
  options: AgentQuestionOptions = {},
): Promise<AgentMessage> {
  await delay(260);
  const scopeHint = options.deviceCode ? `（设备范围：${options.deviceCode}）` : "（系统范围）";
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: `已收到问题：“${question}”${scopeHint}。后续这里会替换成真实智能体接口返回内容。`,
  };
}
