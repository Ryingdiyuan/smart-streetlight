import { mockAgentMessages, mockPromptOptions } from "@/mock/data";
import type { AgentMessage, AgentPromptOption } from "@/types/models";

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

export async function sendQuestion(question: string): Promise<AgentMessage> {
  await delay(260);
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: `已收到问题：“${question}”。后续这里会替换成真实智能体接口返回内容。`,
  };
}
