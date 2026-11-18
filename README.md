# Turium AI — Minimal Knowledge Inbox (RAG Application)

A full-stack, local-first **Retrieval-Augmented Generation (RAG)** application designed to ingest unstructured documents and web pages, index them into a vectorized SQLite document store via an asynchronous queue, and answer natural language queries strictly grounded in the ingested content with interactive source citations.

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                  Frontend (React + Vite)                          |
|  - Ingestion Panel: Custom chunk size (100-2000) & overlap (0-500) sliders        |
|  - Q&A Interface: Natural language prompt input + Top-K selector                  |
|  - Grounded Answer Display: GFM Tables, Headings, and Code Syntax Formatting     |
|  - Citation Inspector: Similarity % badges, chunk offsets, and verbatim snippets   |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST API (/ingest, /query, /items)
                                           v
+-----------------------------------------------------------------------------------+
|                                 Backend (FastAPI)                                 |
|                                                                                   |
|  [Ingestion Pipeline]                                                             |
|   1. Raw Note or Web URL -> Sanitizer / HTTPX HTML Fetcher                        |
|   2. Unstructured Element Chunker (Chunk size & overlap aware)                    |
|   3. 384-dim Dense Vector Embedder                                                |
|   4. Async Document Store Queue (asyncio.Queue worker serializing SQLite writes)  |
|                                                                                   |
|  [RAG & Query Pipeline]                                                           |
|   1. User Query -> Dense Embedding Vector                                         |
|   2. SQLite Cosine Similarity Search                                              |
|   3. Strict Relevance Gate (Threshold filtering against out-of-domain queries)     |
|   4. Grounded Synthesis Prompt -> Groq / OpenAI LLM (or Local Deterministic Fallback)
|   5. Verbatim Source Citation Mapping                                             |
+-----------------------------------------------------------------------------------+
```

---

## Key Features

- **Unstructured Document Ingestion**: Supports unstructured text notes and server-fetched URLs with HTML stripping and boilerplate removal.
- **Dynamic Chunking Controls**: Chunk size (100–2000) and overlap (0–500) configurable directly from the UI or via API.
- **Asynchronous Document Store Queue**: An in-memory `asyncio.Queue` background worker serializes writes to SQLite, ensuring concurrency safety and non-blocking API responses during heavy ingestion.
- **Strict Relevance Filter Gate**: Automatically rejects out-of-domain queries (e.g. asking about recipes when notes are about Python) to prevent hallucinations.
- **Rich GFM Markdown Formatting**: LLM answers render GitHub-Flavored Markdown tables, headings, bulleted lists, and code blocks cleanly.
- **Transparent Evidence Citations**: Every answer includes expandable citation cards displaying similarity match percentages, source document titles, and verbatim chunk evidence.
- **Zero-Dependency Fallback**: Works 100% out of the box with a built-in deterministic local embedder and extractive synthesizer, or seamlessly elevates to Groq (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`) or OpenAI when configured.

---

## Design Decisions & Tradeoffs

| Decision | Tradeoff / Rationale |
| :--- | :--- |
| **SQLite Vector Store vs External Vector DB (e.g., Pinecone, Milvus)** | **Decision**: SQLite with JSON-serialized dense vectors and Python cosine similarity.<br>**Tradeoff**: External vector DBs require running Docker containers or paying for managed cloud clusters. For a lightweight, self-contained Knowledge Inbox, SQLite provides instant setup, zero external infrastructure, and full portability. For enterprise scale (1M+ chunks), migration to pgvector or Qdrant would be preferred. |
| **Async Queue Worker for Writes** | **Decision**: Background `asyncio.Queue` worker serializing database writes.<br>**Tradeoff**: SQLite has a single-writer concurrency model (`database is locked` under concurrent async writes). The async queue completely eliminates write lock contention while keeping HTTP `/ingest` endpoints snappy and responsive. |
| **Unstructured Chunking vs Character Splitting** | **Decision**: Unstructured partition chunking respecting natural syntactic and paragraph boundaries.<br>**Tradeoff**: Unstructured chunking takes slightly more CPU cycles than naive string slicing, but yields far superior semantic coherence for embeddings, avoiding fragmented sentences. |
| **Strict Relevance Filter Gate** | **Decision**: Cosine similarity cutoff gate before passing context to LLM.<br>**Tradeoff**: Lower-scoring chunks that are marginal or irrelevant are pruned before LLM synthesis. If no chunks meet the threshold, the system immediately returns a clean "no relevant knowledge" notice rather than letting the LLM hallucinate answers. |
| **Dual Provider LLM Strategy (Groq + OpenAI + Local Fallback)** | **Decision**: Prioritizes Groq for near-instant inference (< 1 second) and OpenAI compatibility, backed by a local extractive engine.<br>**Tradeoff**: Guarantees the application can run in air-gapped or zero-API-key environments without crashing, while offering cutting-edge speed when API keys are provided. |

---

## Prerequisites

- **Python**: Version 3.10+ (tested on Python 3.11, 3.12, 3.14)
- **Node.js**: Version 18+ (tested on Node 20+)
- **Git**

---

## Local Setup & Quick Start

### 1. Clone the Repository
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd "Turium AI"
```

---

### 2. Backend Setup (FastAPI)

1. Open a terminal and navigate to `BE`:
   ```bash
   cd BE
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Windows (cmd.exe)
   .\.venv\Scripts\activate.bat

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   # Copy sample environment configuration
   cp .env.example .env
   ```
   *(Optional)*: Open `.env` and add your free [Groq API Key](https://console.groq.com/keys) or OpenAI API Key for high-speed LLM answer generation:
   ```ini
   GROQ_API_KEY="your-groq-api-key-here"
   GROQ_MODEL="openai/gpt-oss-120b"
   USE_EXTERNAL_LLM=true
   ```
   *Note: If no API key is provided, the backend automatically uses the built-in deterministic local RAG engine.*

5. Run the backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - **Backend API**: `http://localhost:8000`
   - **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

---

### 3. Frontend Setup (React + Vite)

1. Open a new terminal and navigate to `FE`:
   ```bash
   cd FE
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   - **Frontend Application**: `http://localhost:5173`
   *(Vite automatically proxies `/api` calls to the FastAPI backend running at `http://127.0.0.1:8000`).*

4. *(Optional)* Build for production:
   ```bash
   npm run build
   ```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check, telemetry, active embedding provider, and queue status |
| `POST` | `/ingest` | Ingest a note or URL with custom `chunk_size` and `chunk_overlap` |
| `GET` | `/items` | List all saved knowledge items with chunk counts and timestamps |
| `GET` | `/items/{item_id}` | Retrieve item details and verbatim extracted chunks |
| `DELETE`| `/items/{item_id}` | Delete knowledge item and cascade-delete vector chunks |
| `POST` | `/query` | Execute RAG semantic search and LLM context synthesis |

---

## Running Verification & Tests

To run the backend test suite:
```bash
cd BE
# Ensure your virtual environment is active
python run_tests.py
```
Or with pytest:
```bash
pytest tests/
```

---

## Project Structure

```
Turium AI/
|-- .gitignore                  # Git ignore rules for node_modules, .env, .venv, *.db
|-- README.md                   # Project documentation & design decisions
|-- BE/                         # Backend (FastAPI + LangChain + Unstructured)
|   |-- app/
|   |   |-- api/                # FastAPI route controllers and Pydantic schemas
|   |   |-- db/                 # SQLite database initialization and schemas
|   |   |-- services/
|   |   |   |-- document_queue.py # Async Document Store Queue (asyncio.Queue)
|   |   |   |-- embeddings.py   # Vector embedding providers (OpenAI / Local)
|   |   |   |-- ingestion.py    # URL fetching and text sanitization
|   |   |   |-- rag.py          # RAG pipeline with relevance gate & LLM synthesis
|   |   |   |-- splitter.py     # Unstructured document chunking
|   |   |   |-- vector_store.py # Cosine similarity search & vector persistence
|   |   |-- config.py           # Application settings
|   |   |-- main.py             # FastAPI entrypoint with lifespan events
|   |-- requirements.txt        # Backend Python dependencies
|   |-- .env.example            # Environment configuration template
|   |-- run_tests.py            # Test suite runner
|-- FE/                         # Frontend (React 18 + TypeScript + Vite + Tailwind)
|   |-- src/
|   |   |-- components/
|   |   |   |-- IngestForm.tsx  # Ingestion controls (sliders for chunk size & overlap)
|   |   |   |-- QueryInterface.tsx # Natural language query search bar
|   |   |   |-- AnswerDisplay.tsx  # GFM markdown tables, headings, and citations
|   |   |   |-- ItemList.tsx    # Saved knowledge items manager
|   |   |   |-- Header.tsx      # Clean navigation bar
|   |   |-- api.ts              # Axios/Fetch API client
|   |   |-- types.ts            # TypeScript interfaces
|   |-- package.json            # Node.js dependencies & scripts
|   |-- vite.config.ts          # Vite build config with backend proxy
```
