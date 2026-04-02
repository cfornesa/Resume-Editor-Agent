import { redactPii } from './pii';
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

const buildSystemPrompt = [
  'You are the Resume Editor Agent career strategist.',
  'Respond in plain English only.',
  'Do not use markdown unless the user explicitly requests it.',
  'Create a complete professional resume from the provided source data.',
  'Do not add skills, tools, or experience that are not explicitly present in the input.',
  'Keep the output ready for direct copy-paste into a document editor.',
].join(' ');

const editSystemPrompt = [
  'You are the Resume Editor Agent career strategist in editing mode.',
  'Respond in plain English only.',
  'Do not use markdown unless the user explicitly requests it.',
  'Apply only the requested change and return the full updated resume.',
  'Do not add skills, tools, or experience that are not explicitly present in the resume or context.',
  'Keep the output ready for direct copy-paste into a document editor.',
].join(' ');

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
  const safeInput = redactPii(formatResumeSeed(data));

  const reply = await runAgentConversation(process.env.AGENT_ID || '', [
    {
      role: 'system',
      content: buildSystemPrompt,
    },
    {
      role: 'user',
      content: `BUILD MODE. Construct a complete professional resume from the data below. Do not add any skills, tools, or experience not explicitly listed.\n\n${safeInput}`,
    },
  ]);

  return {
    reply: reply || 'Error: Empty response from model.',
    phase: 'build',
  };
}

export async function editResume(
  currentResume: string,
  userMessage: string,
  history: ResumeHistoryEntry[] = [],
): Promise<{ reply: string; phase: 'edit' }> {
  const documentContext = await getRelevantDocumentContext(`${currentResume}\n\n${userMessage}`.trim());
  const inputs: ConversationInput[] = [
    {
      role: 'system' as const,
      content: editSystemPrompt,
    },
  ];

  for (const entry of history) {
    if (!entry.content) {
      continue;
    }

    inputs.push({
      role: entry.role || 'user',
      content: entry.content,
    });
  }

  inputs.push({
    role: 'user' as const,
    content: [
      'EDIT MODE. Apply only the change requested below to the resume. Return the full updated resume.',
      documentContext ? `\nLocal document context:\n${documentContext}` : '',
      `\nCurrent Resume:\n${currentResume}`,
      `\nEdit Request: ${userMessage}`,
    ].join('\n'),
  });

  const reply = await runAgentConversation(process.env.AGENT_ID || '', inputs);

  return {
    reply: reply || 'Error: Empty response from model.',
    phase: 'edit',
  };
}
