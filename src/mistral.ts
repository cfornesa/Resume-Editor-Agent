type ChatMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export type ConversationInput = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

const MISTRAL_BASE_URL = 'https://api.mistral.ai/v1';

async function fetchJson<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const responseText = await response.text();

  if (!response.ok) {
    throw new Error(`Mistral request failed (${response.status}): ${responseText}`);
  }

  return JSON.parse(responseText) as T;
}

function normalizeContent(content: unknown): string {
  if (typeof content === 'string') {
    return content;
  }

  if (Array.isArray(content) && content.length > 0) {
    const firstPart = content[0] as { text?: string } | undefined;
    return firstPart?.text || '';
  }

  return '';
}

function stripFormatting(text: string): string {
  return text
    .replace(/#{1,6}\s*/g, '')
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
    .replace(/_{1,2}([^_]+)_{1,2}/g, '$1')
    .replace(/[–—]/g, '-')
    .replace(/[\u2600-\u27BF]/g, '')
    .replace(/[\u{1F000}-\u{1FFFF}]/gu, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function extractAssistantText(payload: unknown): string {
  if (!payload || typeof payload !== 'object') {
    return '';
  }

  const conversationPayload = payload as {
    outputs?: Array<{ role?: string; content?: unknown }>;
    messages?: Array<{ role?: string; content?: unknown }>;
    choices?: Array<{ message?: { content?: unknown } }>;
  };

  for (const output of conversationPayload.outputs || []) {
    if (output.role === 'assistant') {
      const content = normalizeContent(output.content);
      if (content) {
        return content;
      }
    }
  }

  for (const message of conversationPayload.messages || []) {
    if (message.role === 'assistant') {
      const content = normalizeContent(message.content);
      if (content) {
        return content;
      }
    }
  }

  const choiceContent = conversationPayload.choices?.[0]?.message?.content;
  return normalizeContent(choiceContent);
}

export async function runAgentConversation(agentId: string, inputs: ConversationInput[]): Promise<string> {
  try {
    const conversationResponse = await fetchJson<Record<string, unknown>>(`${MISTRAL_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.MISTRAL_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        agent_id: agentId,
        inputs,
      }),
    });

    const assistantText = stripFormatting(extractAssistantText(conversationResponse));
    if (assistantText) {
      return assistantText;
    }
  } catch {
    // Fall back to the OpenAI-compatible chat API if the conversations endpoint is unavailable.
  }

  const messages: ChatMessage[] = inputs.map((input) => ({
    role: input.role,
    content: input.content,
  }));

  const chatResponse = await fetchJson<{ choices?: Array<{ message?: { content?: unknown } }> }>(`${MISTRAL_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.MISTRAL_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'mistral-medium-latest',
      messages,
      temperature: 0.2,
      max_tokens: 1500,
    }),
  });

  return stripFormatting(normalizeContent(chatResponse.choices?.[0]?.message?.content));
}

export async function createEmbedding(text: string): Promise<number[]> {
  const response = await fetchJson<{ data?: Array<{ embedding?: number[] }> }>(`${MISTRAL_BASE_URL}/embeddings`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.MISTRAL_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'mistral-embed',
      input: [text],
    }),
  });

  const embedding = response.data?.[0]?.embedding;
  if (!embedding || embedding.length === 0) {
    throw new Error('Empty embedding response from Mistral.');
  }

  return embedding;
}
