import { IngestItemRequest, IngestResponse, KnowledgeItem, QueryResponse, SystemHealth } from './types';

const API_BASE = '/api';
const DEFAULT_TIMEOUT_MS = 15000;

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

export async function checkHealth(): Promise<SystemHealth> {
  const res = await fetchWithTimeout(`${API_BASE}/health`, {}, 10000);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchItems(): Promise<KnowledgeItem[]> {
  const res = await fetchWithTimeout(`${API_BASE}/items`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch items (${res.status})`);
  }
  return res.json();
}

export async function ingestContent(payload: IngestItemRequest): Promise<IngestResponse> {
  const res = await fetchWithTimeout(`${API_BASE}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 30000); // 30s timeout for URL fetching and embedding

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Ingestion failed with status: ${res.status}`);
  }

  return res.json();
}

export async function deleteItem(id: string): Promise<void> {
  const res = await fetchWithTimeout(`${API_BASE}/items/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete item (${res.status})`);
  }
}

export async function submitQuery(question: string, topK: number = 3): Promise<QueryResponse> {
  const res = await fetchWithTimeout(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  }, 20000);

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed with status: ${res.status}`);
  }

  return res.json();
}
