# Resume Editor Agent

## Overview
A Node.js and Express application for building and editing resumes with Mistral AI. The app keeps the current build/chat UX while adding a local PDF/DOCX RAG corpus for targeted context retrieval.

## Project Structure
- `server.ts` - TypeScript entrypoint for Express
- `src/` - server logic, Mistral helpers, and RAG utilities
- `public/` - browser assets served statically
- `documents/` - PDF/DOCX source files for local indexing
- `data/` - on-disk index metadata

## API Endpoints
- `GET /` - Serves the browser UI
- `GET /health` - Health check endpoint
- `POST /build` - Resume generation endpoint
- `POST /chat` - Resume editing endpoint
- `POST /api/rag/reindex` - Rebuilds the local document index

## Environment
- `NODE_ENV` - Development or production mode
- `MISTRAL_API_KEY` - Mistral API key
- `AGENT_ID` - Mistral agent identifier
- `APP_URL` - Public application URL

## Deployment
Configured for Node.js deployment on Hostinger with `npm run build` producing `server.bundle.js`.
