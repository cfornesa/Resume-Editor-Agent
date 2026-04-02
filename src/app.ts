import path from 'node:path';
import express from 'express';
import cors from 'cors';
import { buildResume, editResume } from './resume';
import { ensureDocumentIndex, getCorpusStatus, rebuildDocumentIndex, warmupDocumentIndex } from './rag';

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export async function createApp() {
  const app = express();
  const publicDirectory = path.join(process.cwd(), 'public');
  const rootIndexPath = path.join(process.cwd(), 'index.html');
  const appUrl = process.env.APP_URL?.trim();

  app.disable('x-powered-by');
  app.use(cors({
    origin: appUrl ? [appUrl, 'http://localhost:5000', 'http://127.0.0.1:5000'] : true,
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  }));
  app.use(express.json({ limit: '2mb' }));
  app.use(express.urlencoded({ extended: true }));
  app.use(express.static(publicDirectory));

  app.get('/health', (_request, response) => {
    response.json({ status: 'ok', environment: process.env.NODE_ENV || 'development' });
  });

  app.get('/', (_request, response) => {
    response.sendFile(rootIndexPath);
  });

  app.post('/build', async (request, response) => {
    const body = request.body ?? {};
    const requiredFields = ['name', 'occupation', 'industry', 'job_description', 'summary', 'skills', 'experience', 'education', 'awards'];

    for (const field of requiredFields) {
      if (!isNonEmptyString(body[field])) {
        return response.status(400).json({ error: 'Missing one or more required resume fields.' });
      }
    }

    const startTime = Date.now();

    try {
      const result = await buildResume({
        name: body.name.trim(),
        occupation: body.occupation.trim(),
        industry: body.industry.trim(),
        jobDescription: body.job_description.trim(),
        summary: body.summary.trim(),
        skills: body.skills.trim(),
        experience: body.experience.trim(),
        education: body.education.trim(),
        awards: body.awards.trim(),
      });

      response.json({
        ...result,
        duration: (Date.now() - startTime) / 1000,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      response.status(500).json({ error: message });
    }
  });

  app.post('/chat', async (request, response) => {
    const body = request.body ?? {};
    const currentResume = body.resume;
    const userMessage = body.message;
    const history = Array.isArray(body.history) ? body.history : [];

    if (!isNonEmptyString(currentResume) || !isNonEmptyString(userMessage)) {
      return response.status(400).json({ error: 'Missing resume or message.' });
    }

    const startTime = Date.now();

    try {
      const result = await editResume(currentResume.trim(), userMessage.trim(), history);
      response.json({
        ...result,
        duration: (Date.now() - startTime) / 1000,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      response.status(500).json({ error: message });
    }
  });

  app.post('/api/rag/reindex', async (_request, response) => {
    try {
      const result = await rebuildDocumentIndex();
      response.json({
        ok: true,
        indexed: result.chunkCount,
        documents: result.documentCount,
        generatedAt: result.generatedAt,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      response.status(500).json({ ok: false, error: message });
    }
  });

  app.get('/api/rag/status', async (_request, response) => {
    try {
      const status = await getCorpusStatus();
      response.json({ ok: true, ...status });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      response.status(500).json({ ok: false, error: message });
    }
  });

  const warmup = async () => {
    await warmupDocumentIndex();
  };

  return { app, warmup };
}
