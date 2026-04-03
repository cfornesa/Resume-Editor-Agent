const FIELD_MAX_LENGTHS = {
  name: 100,
  occupation: 150,
  industry: 150,
  jobDescription: 3000,
  summary: 1500,
  skills: 1500,
  experience: 5000,
  education: 1500,
  awards: 1000,
} as const;

const CHAT_MESSAGE_MAX_LENGTH = 2000;

// Patterns that signal prompt injection attempts against the agent
const INJECTION_PATTERNS: RegExp[] = [
  /ignore\s+(all\s+)?(previous|prior|above)\s+instructions?/gi,
  /forget\s+(everything|all(\s+previous)?)/gi,
  /you\s+are\s+now\s+(a|an)\b/gi,
  /\[INST\]/g,
  /<\s*\/?system\s*>/gi,
  /^(system|assistant)\s*:/gim,
];

function stripHtml(text: string): string {
  return text.replace(/<[^>]+>/g, '');
}

function neutralizeInjections(text: string): string {
  let result = text;
  for (const pattern of INJECTION_PATTERNS) {
    pattern.lastIndex = 0;
    result = result.replace(pattern, '[FILTERED]');
  }
  return result;
}

function sanitizeField(value: string, maxLength: number): string {
  return neutralizeInjections(stripHtml(value.trim())).slice(0, maxLength);
}

export type ResumeFields = {
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

export function sanitizeResumeData(data: ResumeFields): ResumeFields {
  return {
    name: sanitizeField(data.name, FIELD_MAX_LENGTHS.name),
    occupation: sanitizeField(data.occupation, FIELD_MAX_LENGTHS.occupation),
    industry: sanitizeField(data.industry, FIELD_MAX_LENGTHS.industry),
    jobDescription: sanitizeField(data.jobDescription, FIELD_MAX_LENGTHS.jobDescription),
    summary: sanitizeField(data.summary, FIELD_MAX_LENGTHS.summary),
    skills: sanitizeField(data.skills, FIELD_MAX_LENGTHS.skills),
    experience: sanitizeField(data.experience, FIELD_MAX_LENGTHS.experience),
    education: sanitizeField(data.education, FIELD_MAX_LENGTHS.education),
    awards: sanitizeField(data.awards, FIELD_MAX_LENGTHS.awards),
  };
}

export function sanitizeChatMessage(message: string): string {
  return sanitizeField(message, CHAT_MESSAGE_MAX_LENGTH);
}
