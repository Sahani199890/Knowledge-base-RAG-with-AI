# AI Knowledge Inbox - Frontend (React + TypeScript + Vite)

Modern, accessible, responsive user interface for the Minimal AI Knowledge Inbox.

## Key Features
- **React 18 + TypeScript**: Type-safe component architecture with clean hooks.
- **Tailwind CSS**: Crisp, clear layout emphasizing content clarity and readability over bloated design.
- **Dual Ingestion**: Easy switching between quick unstructured text notes and server-fetched URLs.
- **RAG Q&A Interface**: Natural language query input with example suggestion chips and retrieval depth controls (top-k).
- **Cited Sources Explorer**: Interactive citation cards displaying similarity match percentage, chunk offsets, and verbatim evidence snippets.
- **Live System Telemetry**: Top bar displays backend status, chunk counters, and active embedding engine.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
Runs at `http://localhost:5173`. API calls are automatically proxied to the backend at `http://localhost:8000`.

### 3. Production Build
```bash
npm run build
```
Generates production-ready static assets in `dist/`.
