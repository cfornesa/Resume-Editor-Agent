export type RuntimeEnv = {
  nodeEnv: string;
  mistralApiKey: string;
  agentId: string;
  appUrl: string;
};

export function loadRuntimeEnv(): RuntimeEnv {
  const nodeEnv = process.env.NODE_ENV?.trim() || 'development';
  const mistralApiKey = process.env.MISTRAL_API_KEY?.trim();
  const agentId = process.env.AGENT_ID?.trim();
  const appUrl = process.env.APP_URL?.trim() || `http://localhost:${process.env.PORT || 5000}`;

  if (!mistralApiKey) {
    throw new Error('MISTRAL_API_KEY missing from environment.');
  }

  if (!agentId) {
    throw new Error('AGENT_ID missing from environment.');
  }

  process.env.NODE_ENV = nodeEnv;
  process.env.APP_URL = appUrl;

  return {
    nodeEnv,
    mistralApiKey,
    agentId,
    appUrl,
  };
}
