# AI Meeting Intelligence System

Full-stack starter for meeting audio → transcript → insights (summary, action items, sentiment) + retrieval-augmented Q&A (RAG) and a simple knowledge-graph view.

## Stack

- Frontend: Next.js (React) + Tailwind
- Backend: FastAPI (Python)
- Database: MongoDB
- Vector DB: ChromaDB
- Models:
  - Whisper (speech-to-text)
  - LLM API (summaries, action items, RAG answers)

## Monorepo layout

```
ai-meeting-intelligence-system/
  backend/
  frontend/
  docker-compose.yml
```

## Quickstart (dev)

1) Start MongoDB

```bash
cd ai-meeting-intelligence-system
docker compose up -d mongodb
```

2) Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

3) Frontend

```bash
cd ../frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## What’s implemented

- Audio upload endpoint that:
  - stores metadata + transcript in MongoDB
  - generates summary + action items + sentiment
  - saves transcript embeddings in ChromaDB
- RAG Q&A endpoint over past meetings
- Next.js pages for:
  - upload
  - meetings list
  - meeting detail (transcript + summary + action items)
  - Q&A chat
  - knowledge graph visualization (meetings ↔ participants ↔ tasks)

## Notes

- Whisper is wired as a provider abstraction. Use local Whisper (`openai-whisper`) or swap to a hosted STT.
- LLM calls are written against an OpenAI-compatible API shape (configurable base URL + API key).
- The knowledge graph is derived from MongoDB documents (no separate graph DB required for this starter).

