import { createPiiRedactor, redactPii, restorePii } from './pii';
import { sanitizeResumeData, sanitizeChatMessage } from './sanitize';
import { getRelevantDocumentContext } from './rag';
import { runAgentConversation, type ConversationInput } from './mistral';

type ResumeHistoryEntry = {
  role?: 'user' | 'assistant' | 'system';
  content?: string;
};

type ResumeRequestData = {
  name: string;
  occupation: string;
  industry: string;
  jobDescription: string;
  summary: string;
  skills: string;
  experience: string;
  education: string;
  awards: string;
};

function formatResumeSeed(data: ResumeRequestData): string {
  return [
    `Name: ${data.name}`,
    `Target Occupation: ${data.occupation}`,
    `Industry: ${data.industry}`,
    `Target JD: ${data.jobDescription}`,
    `Summary: ${data.summary}`,
    `Skills: ${data.skills}`,
    `Experience: ${data.experience}`,
    `Education: ${data.education}`,
    `Awards: ${data.awards}`,
  ].join('\n');
}

export async function buildResume(data: ResumeRequestData): Promise<{ reply: string; phase: 'build' }> {
  const sanitized = sanitizeResumeData(data);
  const { redacted: safeInput, map } = redactPii(formatResumeSeed(sanitized));

  const rawReply = await runAgentConversation(process.env.AGENT_ID || '', [
    {
      role: 'user',
      content: `BUILD MODE. Construct a complete professional resume from the data below. Do not add any skills, tools, or experience not explicitly listed.\n\n${safeInput}`,
    },
  ]);

  return {
    reply: restorePii(rawReply || 'Error: Empty response from model.', map),
    phase: 'build',
  };
}

export async function editResume(
  currentResume: string,
  userMessage: string,
  history: ResumeHistoryEntry[] = [],
): Promise<{ reply: string; phase: 'edit' }> {
  const safeUserMessage = sanitizeChatMessage(userMessage);

  // Use a single redactor across all inputs so tokens are unique and the
  // restore map covers every string sent to the agent.
  const redactor = createPiiRedactor();
  const safeResume = redactor.redact(currentResume);
  const safeMessage = redactor.redact(safeUserMessage);

  const documentContext = await getRelevantDocumentContext(`${safeResume}\n\n${safeMessage}`.trim());
  const inputs: ConversationInput[] = [];

  for (const entry of history) {
    // Drop system-role history entries — they should not originate from the client.
    if (!entry.content || entry.role === 'system') {
      continue;
    }

    // Redact user-sourced history; leave assistant messages from the agent as-is.
    const content = entry.role === 'assistant'
      ? entry.content
      : redactor.redact(entry.content);

    inputs.push({ role: entry.role || 'user', content });
  }

  inputs.push({
    role: 'user' as const,
    content: [
      'EDIT MODE. Apply only the change requested below to the resume. Return the full updated resume.',
      documentContext ? `\nLocal document context:\n${documentContext}` : '',
      `\nCurrent Resume:\n${safeResume}`,
      `\nEdit Request: ${safeMessage}`,
    ].join('\n'),
  });

  const rawReply = await runAgentConversation(process.env.AGENT_ID || '', inputs);

  return {
    reply: restorePii(rawReply || 'Error: Empty response from model.', redactor.map),
    phase: 'edit',
  };
}
