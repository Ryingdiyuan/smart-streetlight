import { mockPromptOptions } from "@/mock/data";
import type { AgentMessage, AgentPromptOption, AgentQuestionOptions } from "@/types/models";

function delay(ms = 220) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

/** In-memory conversation store for mock mode */
const conversation: AgentMessage[] = [];

export async function getPromptOptions(): Promise<AgentPromptOption[]> {
  await delay();
  return structuredClone(mockPromptOptions);
}

export async function getConversation(): Promise<AgentMessage[]> {
  await delay();
  return structuredClone(conversation);
}

export async function sendQuestion(
  question: string,
  options: AgentQuestionOptions = {},
): Promise<AgentMessage> {
  // Push user question to in-memory store
  conversation.push({
    id: `user-${Date.now()}`,
    role: "user",
    content: question,
  });

  await delay(260);

  const scopeHint = options.deviceCode
    ? `（设备范围：${options.deviceCode}）`
    : "（系统范围）";
  const answer: AgentMessage = {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: `已收到问题：“${question}”${scopeHint}。后续这里会替换成真实智能体接口返回内容。`,
  };

  // Push assistant answer to in-memory store
  conversation.push(answer);

  return answer;
}

export async function clearHistory(): Promise<void> {
  await delay(100);
  conversation.length = 0;
}
