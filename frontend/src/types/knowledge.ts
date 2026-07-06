// Knowledge base types
export interface KnowledgeDocument {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  chunk_count: number;
  uploaded_by: number | null;
  description: string | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  token_count: number;
  embedding_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

export interface SearchTestResult {
  content: string;
  document_name: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface DocumentDetail extends KnowledgeDocument {
  chunks: DocumentChunk[];
}