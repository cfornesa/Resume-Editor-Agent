export type PiiMap = Record<string, string>;

const PII_PATTERNS: Array<[string, RegExp]> = [
  ['EMAIL', /[\w.-]+@[\w.-]+\.\w+/gi],
  ['PHONE', /\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g],
  ['SSN', /\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b/g],
  ['ADDRESS', /\d{1,5}\s\w+\.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}/gi],
];

class PiiRedactor {
  private counter = 0;
  readonly map: PiiMap = {};

  redact(text: string): string {
    let result = text;
    for (const [label, pattern] of PII_PATTERNS) {
      pattern.lastIndex = 0;
      result = result.replace(pattern, (match) => {
        const token = `[${label}_REDACTED_${this.counter++}]`;
        this.map[token] = match;
        return token;
      });
    }
    return result;
  }
}

export function createPiiRedactor(): PiiRedactor {
  return new PiiRedactor();
}

export function redactPii(text: string): { redacted: string; map: PiiMap } {
  const redactor = createPiiRedactor();
  return { redacted: redactor.redact(text), map: redactor.map };
}

export function restorePii(text: string, map: PiiMap): string {
  let result = text;
  for (const [token, value] of Object.entries(map)) {
    result = result.split(token).join(value);
  }
  return result;
}
