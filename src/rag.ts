import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import mammoth from 'mammoth';
import pdfParse from 'pdf-parse';
import { createEmbedding } from './mistral';

type DocumentChunk = {
  id: string;
  source: string;
  text: string;
  embedding: number[];
};

type DocumentIndex = {
  generatedAt: string;
  documentCount: number;
  chunkCount: number;
  corpusSignature: string;
  chunks: DocumentChunk[];
};

export type CorpusStatus = {
  documentCount: number;
  indexedDocumentCount: number;
  indexedChunkCount: number;
  generatedAt: string | null;
  corpusSignature: string;
  indexedCorpusSignature: string | null;
  stale: boolean;
};

const workspaceRoot = process.cwd();
const documentsDir = path.join(workspaceRoot, 'documents');
const dataDir = path.join(workspaceRoot, 'data');
const indexPath = path.join(dataDir, 'rag-index.json');
const supportedExtensions = new Set(['.pdf', '.docx', '.txt', '.md']);
let inMemoryIndex: DocumentIndex | null = null;
let inMemoryIndexLoaded = false;
let rebuildPromise: Promise<DocumentIndex> | null = null;

function chunkText(text: string, chunkSize = 1200, overlap = 200): string[] {
  const normalizedText = text.replace(/\r\n/g, '\n').replace(/[ \t]+/g, ' ').trim();
  if (!normalizedText) {
    return [];
  }

  const chunks: string[] = [];
  let start = 0;

  while (start < normalizedText.length) {
    const end = Math.min(start + chunkSize, normalizedText.length);
    const chunk = normalizedText.slice(start, end).trim();
    if (chunk) {
      chunks.push(chunk);
    }
    if (end === normalizedText.length) {
      break;
    }
    start = Math.max(end - overlap, start + 1);
  }

  return chunks;
}

async function ensureDirectories() {
  await fs.mkdir(documentsDir, { recursive: true });
  await fs.mkdir(dataDir, { recursive: true });
}

async function listDocumentFiles(directory: string): Promise<string[]> {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const filePaths: string[] = [];

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      filePaths.push(...await listDocumentFiles(fullPath));
      continue;
    }

    if (supportedExtensions.has(path.extname(entry.name).toLowerCase())) {
      filePaths.push(fullPath);
    }
  }

  return filePaths.sort((left, right) => left.localeCompare(right));
}

async function extractDocumentText(filePath: string): Promise<string> {
  const extension = path.extname(filePath).toLowerCase();
  const buffer = await fs.readFile(filePath);

  if (extension === '.pdf') {
    const parsed = await pdfParse(buffer);
    return parsed.text || '';
  }

  if (extension === '.docx') {
    const parsed = await mammoth.extractRawText({ buffer });
    return parsed.value || '';
  }

  if (extension === '.txt' || extension === '.md') {
    return buffer.toString('utf8');
  }

  return '';
}

async function createCorpusSignature(documentFiles: string[]): Promise<string> {
  if (documentFiles.length === 0) {
    return 'empty-corpus';
  }

  const hasher = crypto.createHash('sha256');
  for (const filePath of documentFiles) {
    const stats = await fs.stat(filePath);
    const relativeSource = path.relative(workspaceRoot, filePath);
    hasher.update(`${relativeSource}:${stats.size}:${stats.mtimeMs.toFixed(0)}\n`);
  }

  return hasher.digest('hex');
}

function cosineSimilarity(left: number[], right: number[]): number {
  const limit = Math.min(left.length, right.length);
  let dotProduct = 0;
  let leftMagnitude = 0;
  let rightMagnitude = 0;

  for (let index = 0; index < limit; index += 1) {
    const leftValue = left[index] ?? 0;
    const rightValue = right[index] ?? 0;
    dotProduct += leftValue * rightValue;
    leftMagnitude += leftValue * leftValue;
    rightMagnitude += rightValue * rightValue;
  }

  if (!leftMagnitude || !rightMagnitude) {
    return 0;
  }

  return dotProduct / (Math.sqrt(leftMagnitude) * Math.sqrt(rightMagnitude));
}

async function persistIndex(index: DocumentIndex): Promise<void> {
  await ensureDirectories();
  await fs.writeFile(indexPath, JSON.stringify(index, null, 2), 'utf8');
  inMemoryIndex = index;
  inMemoryIndexLoaded = true;
}

async function loadPersistedIndex(): Promise<DocumentIndex | null> {
  if (inMemoryIndexLoaded) {
    return inMemoryIndex;
  }

  try {
    const rawIndex = await fs.readFile(indexPath, 'utf8');
    const parsed = JSON.parse(rawIndex) as DocumentIndex;
    inMemoryIndex = parsed;
    inMemoryIndexLoaded = true;
    return parsed;
  } catch {
    inMemoryIndex = null;
    inMemoryIndexLoaded = true;
    return null;
  }
}

export async function rebuildDocumentIndex(): Promise<DocumentIndex> {
  if (rebuildPromise) {
    return rebuildPromise;
  }

  rebuildPromise = (async () => {
    await ensureDirectories();
    const documentFiles = await listDocumentFiles(documentsDir);
    const corpusSignature = await createCorpusSignature(documentFiles);
    const chunks: DocumentChunk[] = [];

    for (const filePath of documentFiles) {
      const extractedText = await extractDocumentText(filePath);
      const chunkTexts = chunkText(extractedText);
      const relativeSource = path.relative(workspaceRoot, filePath);

      for (let chunkIndex = 0; chunkIndex < chunkTexts.length; chunkIndex += 1) {
        const chunkTextValue = chunkTexts[chunkIndex];
        const embedding = await createEmbedding(chunkTextValue);
        chunks.push({
          id: `${relativeSource}:${chunkIndex}`,
          source: relativeSource,
          text: chunkTextValue,
          embedding,
        });
      }
    }

    const index: DocumentIndex = {
      generatedAt: new Date().toISOString(),
      documentCount: documentFiles.length,
      chunkCount: chunks.length,
      corpusSignature,
      chunks,
    };

    await persistIndex(index);
    return index;
  })();

  try {
    return await rebuildPromise;
  } finally {
    rebuildPromise = null;
  }
}

export async function ensureDocumentIndex(): Promise<DocumentIndex | null> {
  await ensureDirectories();
  const documentFiles = await listDocumentFiles(documentsDir).catch(() => []);
  const currentSignature = await createCorpusSignature(documentFiles);
  const persistedIndex = await loadPersistedIndex();
  if (
    persistedIndex
    && persistedIndex.chunkCount > 0
    && persistedIndex.corpusSignature === currentSignature
  ) {
    return persistedIndex;
  }

  if (documentFiles.length === 0) {
    return persistedIndex;
  }

  return rebuildDocumentIndex();
}

export async function getRelevantDocumentContext(query: string, topK = 4): Promise<string> {
  const documentIndex = await ensureDocumentIndex();
  if (!documentIndex || documentIndex.chunks.length === 0) {
    return '';
  }

  const queryEmbedding = await createEmbedding(query);
  const scoredChunks = documentIndex.chunks
    .map((chunk) => ({
      chunk,
      score: cosineSimilarity(queryEmbedding, chunk.embedding),
    }))
    .sort((left, right) => right.score - left.score)
    .slice(0, topK)
    .filter((entry) => entry.score > 0.1);

  if (scoredChunks.length === 0) {
    return '';
  }

  return scoredChunks
    .map(({ chunk, score }) => `Source: ${chunk.source}\nRelevance: ${score.toFixed(3)}\n${chunk.text}`)
    .join('\n\n---\n\n');
}

export async function warmupDocumentIndex(): Promise<void> {
  await ensureDocumentIndex();
}

export async function getCorpusStatus(): Promise<CorpusStatus> {
  await ensureDirectories();
  const documentFiles = await listDocumentFiles(documentsDir).catch(() => []);
  const currentSignature = await createCorpusSignature(documentFiles);
  const persistedIndex = await loadPersistedIndex();

  return {
    documentCount: documentFiles.length,
    indexedDocumentCount: persistedIndex?.documentCount || 0,
    indexedChunkCount: persistedIndex?.chunkCount || 0,
    generatedAt: persistedIndex?.generatedAt || null,
    corpusSignature: currentSignature,
    indexedCorpusSignature: persistedIndex?.corpusSignature || null,
    stale: !persistedIndex || persistedIndex.corpusSignature !== currentSignature,
  };
}
