// Chat types
export interface ChatSession {
  id: number;
  user_id: number;
  title: string;
  status: string;
  message_count: number;
  last_message: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CitationItem {
  chunk_id: number;
  content: string;
  document_name: string;
  score: number;
}

export interface Message {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  citations: CitationItem[] | null;
  token_count: number;
  created_at: string | null;
}

export interface SSEEvent {
  type: 'text' | 'end' | 'error';
  content?: string;
  citations?: CitationItem[];
  token_count?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}