# AI Meeting Intelligence System — Complete Workflow

A full-stack application that turns meeting audio into transcripts, insights (summary, action items, sentiment), RAG Q&A, and a knowledge graph.

---

## 1. Project Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│                         http://localhost:3000                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                         http://localhost:8000                                │
│  • Whisper (speech-to-text)  • LLM (summaries, action items)  • ChromaDB     │
└───────────┬─────────────────────────────┬───────────────────────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────┐     ┌───────────────────────────────────────────────┐
│   MongoDB (aimis)     │     │   ChromaDB (vector embeddings)                 │
│   • meetings          │     │   • meeting_transcripts                        │
│   • meeting_transcripts│    └───────────────────────────────────────────────┘
│   • tasks             │
│   • task_tracker      │
└───────────────────────┘
```

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | FastAPI (Python), Motor (async MongoDB) |
| Database | MongoDB |
| Vector DB | ChromaDB (embeddings for RAG) |
| Speech-to-Text | Whisper (local, `openai-whisper`) |
| LLM | OpenAI-compatible API or Gemini |
| Embeddings | Hash-based fallback (replace with real model for production RAG) |

---

## 3. Setup & Startup (Step-by-Step)

### Prerequisites
- Docker Desktop (for MongoDB)
- Python 3.10+
- Node.js 18+
- API key: OpenAI or Gemini

### Step 1: Start MongoDB

```powershell
cd c:\Users\anush\OneDrive\Desktop\GEMSCAP\ai-meeting-intelligence-system
docker compose up -d mongodb
```

### Step 2: Configure Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend\.env` and set:
- `LLM_API_KEY` (OpenAI) or `GEMINI_API_KEY`
- `JWT_SECRET` (random string for auth)

### Step 3: Start Backend

```powershell
uvicorn app.main:app --reload --port 8000
```

### Step 4: Configure & Start Frontend

```powershell
cd ..\frontend
npm install
copy .env.local.example .env.local
npm run dev
```

### Step 5: Open the App

Open **http://localhost:3000** in your browser.

---

## 4. Data Flow (What Happens When You Upload)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Upload      │     │  Whisper     │     │  MongoDB     │     │  ChromaDB    │
│  Audio       │ ──► │  Transcribe  │ ──► │  meetings    │ ──► │  Embeddings  │
│  (.mp3 etc)  │     │  to text     │     │  (metadata)  │     │  (for RAG)   │
└──────────────┘     └──────────────┘     └──────┬───────┘     └──────────────┘
                                                 │
                                                 ▼
                                        ┌──────────────┐
                                        │  LLM         │
                                        │  Summary,    │
                                        │  Key points, │
                                        │  Action items│
                                        └──────┬───────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  MongoDB     │
                                        │  tasks       │
                                        │  (action     │
                                        │   items)     │
                                        └──────────────┘
```

### Step-by-step (detailed)

| Step | What happens |
|------|--------------|
| **1. Upload** | User selects audio file (`.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.webm`), optionally adds title and comma-separated participants. |
| **2. Whisper** | Audio is sent to OpenAI Whisper (local model). It converts speech → text. Uses `WHISPER_MODEL` (default `base`). |
| **3. Sentiment** | Transcript is analyzed with a simple lexicon (positive/negative words). Output: `label` (positive/neutral/negative), `score`, `pos_ratio`, `neg_ratio`. |
| **4. MongoDB (first write)** | A meeting document is created with: `title`, `participants`, `transcript_text`, `sentiment`, and placeholder `summary`, `key_points`, `action_items`. |
| **5. ChromaDB** | Transcript is split into chunks (max 1200 chars, 200 overlap). Each chunk gets an embedding (hash-based fallback or real model). Stored so **RAG Q&A** can find relevant passages later. |
| **6. LLM — Summary** | LLM receives the transcript and returns a concise bullet-point summary. |
| **7. LLM — Key points** | LLM extracts up to 10 important points as JSON (`{"points": ["...", ...]}`). Falls back to heuristic extraction if no API key. |
| **8. LLM — Action items** | LLM extracts tasks as JSON (`{"items": [{"title": "...", "owner": "...", "due_date": "..."}]}`). |
| **9. MongoDB (update)** | Meeting doc is updated with `summary`, `key_points`, `action_items`. |
| **10. MongoDB (tasks)** | Each action item is inserted into `tasks` with `meeting_id`, `title`, `assignee`, `due_date`, `status: "open"`. |

### LLM providers

- **OpenAI-compatible**: set `LLM_API_KEY` and optionally `LLM_BASE_URL`, `LLM_MODEL`.
- **Gemini**: set `GEMINI_API_KEY` and optionally `GEMINI_MODEL`.

### RAG Q&A flow (`/ask`)

1. User asks a question.
2. Question is embedded and sent to ChromaDB.
3. ChromaDB returns top-k similar transcript chunks.
4. LLM receives question + chunks and generates an answer grounded in that context.

---

## 5. MongoDB Structure (`aimis` Database)

| Collection | Purpose | Key fields |
|------------|---------|------------|
| `meetings` | Full meeting record | `title`, `participants`, `transcript_text`, `summary`, `key_points`, `sentiment`, `action_items`, `created_at` |
| `meeting_transcripts` | Transcript API storage | `meeting_id`, `meeting_title`, `transcript`, `summary`, `sentiment` |
| `tasks` | Action items from meetings | `meeting_id`, `title`, `assignee`, `due_date`, `status` |
| `task_tracker` | Task status workflow | `task_id`, `meeting_id`, `status` (open / in progress / done) |
| `user_logins` | Who used the system (login/register) | `email`, `name`, `source`, `logged_in_at` |

**Note:** The database and collections are created automatically when the backend inserts data.

---

## 6. Frontend Pages & Features

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Landing / dashboard |
| Upload | `/upload` | Upload meeting audio, add title & participants |
| Meetings | `/meetings` | List all meetings (up to 10,000) |
| Meeting Detail | `/meetings/[id]` | Full transcript, summary, key points, action items, sentiment |
| Task Dashboard | `/dashboard/[id]` | Task tracker for a meeting; update status (open → in progress → done) |
| Ask (RAG) | `/ask` | Type a question; answers use relevant transcript chunks from ChromaDB |
| Graph | `/graph` | Visual graph: **meetings** ↔ **participants** (attended) ↔ **tasks** (owned by) |
| Login | `/login` | User authentication |
| Register | `/register` | User registration |

### Knowledge graph

The graph builds **nodes** (meetings, people, tasks) and **edges** (attended, has_task, owns) from MongoDB. No separate graph DB; data comes from `meetings` and `action_items`.

---

## 7. Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/log-login` | Record a login/register event (stores in `user_logins`) |
| POST | `/meetings` | Upload audio, transcribe, generate insights |
| GET | `/meetings` | List meetings (up to 10,000) |
| GET | `/meetings/{id}` | Get meeting detail |
| GET | `/meetings/{id}/tasks` | Get tasks for a meeting |
| POST | `/meetings/ask` | RAG Q&A over meetings |
| GET | `/graph` | Knowledge graph data |
| GET/POST | `/transcripts/*` | Transcript CRUD |
| GET/POST/PATCH/DELETE | `/tasks` | Task tracker operations |
| POST | `/transcribe` | Transcribe only (no storage) |
| GET | `/health` | Health check |

---

## 8. Viewing Data in MongoDB Compass

1. Connect to `localhost:27017`
2. Click **Refresh** (F5)
3. Select the **`aimis`** database
4. Click each collection to view documents:
   - `meetings` — meeting records
   - `meeting_transcripts` — transcript records
   - `tasks` — action items
   - `task_tracker` — task status
   - `user_logins` — who logged in or registered (email, name, when)

---

## 9. Configuration Reference

### Backend (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_URI | MongoDB connection | mongodb://localhost:27017 |
| MONGODB_DB | Database name | aimis |
| CHROMA_PERSIST_DIR | ChromaDB storage | ./storage/chroma |
| LLM_API_KEY | OpenAI API key | — |
| GEMINI_API_KEY | Gemini API key | — |
| LLM_MODEL | LLM model name | gpt-4o-mini |
| WHISPER_MODEL | Whisper model | base |

### Frontend (`.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_BASE | Backend URL | http://localhost:8000 |

---

## 10. Quick Reference Commands

```powershell
# Start MongoDB
cd c:\Users\anush\OneDrive\Desktop\GEMSCAP\ai-meeting-intelligence-system
docker compose up -d mongodb

# Start Backend
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Start Frontend (new terminal)
cd frontend
npm run dev

# Stop MongoDB
docker compose down
```

---

## 11. Customizations We Applied

- **Increased list limits** from 50/100/200 to 10,000 for:
  - Meetings list
  - Transcripts list
  - Tasks
  - Knowledge graph

This lets you view all stored records in the app and in MongoDB.
