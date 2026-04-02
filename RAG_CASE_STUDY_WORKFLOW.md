# Case Study Embedding Workflow

This project uses local Retrieval-Augmented Generation (RAG) for chatbot context.

## 1) Put source files in the corpus folder

Place case-study files in `documents/`.

Supported formats:
- `.docx`
- `.pdf`
- `.txt`
- `.md`

## 2) Ensure required environment variables are set

Required variables:
- `MISTRAL_API_KEY`
- `AGENT_ID`
- `NODE_ENV`
- `APP_URL`

## 3) Build the server bundle

```bash
npm run build
```

## 4) Generate embeddings and rebuild the index

```bash
npm run rag:index
```

This command reads files from `documents/`, chunks them, generates embeddings, and writes `data/rag-index.json`.

## 5) Run the server

```bash
npm start
```

## 6) Confirm corpus/index status

```bash
curl -s http://127.0.0.1:5000/api/rag/status
```

Status payload includes:
- `documentCount`: files currently in `documents/`
- `indexedDocumentCount`: files reflected in the index
- `indexedChunkCount`: total stored chunks
- `stale`: whether source files changed since last indexing

## 7) Force a full reindex at any time

```bash
curl -s -X POST http://127.0.0.1:5000/api/rag/reindex
```

Use this after editing or replacing case-study files.
