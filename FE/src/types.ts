export type SourceType = 'note' | 'url';

export interface IngestItemRequest {
  type: SourceType;
  content: string;
  title?: string;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface IngestResponse {
  id: string;
  type: SourceType;
  title: string;
  url?: string | null;
  chunk_count: number;
  content_length: number;
  created_at: string;
  preview: string;
}

export interface KnowledgeItem {
  id: string;
  type: SourceType;
  title: string;
  content: string;
  url?: string | null;
  chunk_count: number;
  created_at: string;
}

export interface SourceCitation {
  source_num: number;
  chunk_id: string;
  item_id: string;
  title: string;
  source_type: SourceType;
  url?: string | null;
  similarity_score: number;
  snippet: string;
  chunk_index: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceCitation[];
  question: string;
  llm_used: string;
}

export interface SystemHealth {
  status: string;
  app: string;
  total_items: number;
  total_chunks: number;
  embedding_provider: string;
  splitter_type: string;
  queue_status?: string;
  queue_metrics?: {
    queue_size: number;
    is_running: boolean;
    processed_count: number;
    failed_count: number;
  };
}
