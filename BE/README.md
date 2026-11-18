# AI Knowledge Inbox - Backend (FastAPI + LangChain + Unstructured)

Production-grade asynchronous Python backend for the Minimal AI Knowledge Inbox.

## Key Features
- **FastAPI**: Async REST API with automatic OpenAPI documentation (`/docs`).
- **LangChain & Unstructured Text Splitter**: Chunks raw notes and scraped web pages respecting natural sentence and paragraph boundaries.
- **Persistent SQLite Vector Store**: Embeds and indexes chunks with cosine similarity search without bloated external infrastructure.
- **RAG Pipeline**: Semantic chunk retrieval and context synthesis with strict source citations.
- **Zero-Dependency Fallback**: Runs completely out of the box with a built-in local deterministic semantic embedder and extractive synthesizer, or seamlessly switches to OpenAI `text-embedding-3-small` and `gpt-4o-mini` when `OPENAI_API_KEY` is provided.

## Quick Start

### 1. Virtual Environment & Dependencies
```bash
# Create virtual environment (already set up in .venv)
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Or on Windows (cmd.exe)
.\.venv\Scripts\activate.bat

# Install dependencies inside venv
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional: Add your `OPENAI_API_KEY` in `.env` if you wish to use OpenAI models).*

### 3. Run the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 4. Run Verification Tests
```bash
python run_tests.py
```
