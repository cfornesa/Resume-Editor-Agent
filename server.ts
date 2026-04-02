import 'dotenv/config';
import { createApp } from './src/app';
import { loadRuntimeEnv } from './src/env';

async function main() {
  loadRuntimeEnv();

  const { app, warmup } = await createApp();
  const port = Number(process.env.PORT || 5000);
  const server = app.listen(port, '0.0.0.0', () => {
    const appUrl = process.env.APP_URL?.trim();
    console.log(`Resume Editor Agent listening on port ${port}${appUrl ? ` (${appUrl})` : ''}`);
  });

  try {
    await warmup();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown warmup error';
    console.warn(`RAG warmup skipped: ${message}`);
  }

  const shutdown = () => {
    server.close(() => process.exit(0));
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

if (process.argv.includes('--index-documents')) {
  import('./src/rag').then(async ({ rebuildDocumentIndex }) => {
    loadRuntimeEnv();
    const result = await rebuildDocumentIndex();
    console.log(`Indexed ${result.chunkCount} chunks from ${result.documentCount} documents.`);
    process.exit(0);
  }).catch((error) => {
    console.error(error);
    process.exit(1);
  });
} else {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
