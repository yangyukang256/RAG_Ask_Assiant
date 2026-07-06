import api from './index';
import type { KnowledgeDocument, DocumentDetail, DocumentChunk, SearchTestResult } from '../types/knowledge';

export const knowledgeApi = {
  listDocuments: (page = 1, pageSize = 20, status?: string) =>
    api.get('/api/v1/knowledge/documents', {
      params: { page, page_size: pageSize, status },
    }),

  uploadDocument: (file: File, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) formData.append('description', description);
    return api.post('/api/v1/knowledge/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getDocument: (id: number) =>
    api.get<DocumentDetail>(`/api/v1/knowledge/documents/${id}`),

  deleteDocument: (id: number) =>
    api.delete(`/api/v1/knowledge/documents/${id}`),

  getChunks: (docId: number, page = 1, pageSize = 50) =>
    api.get(`/api/v1/knowledge/documents/${docId}/chunks`, {
      params: { page, page_size: pageSize },
    }),

  reprocessDocument: (docId: number) =>
    api.post(`/api/v1/knowledge/documents/${docId}/reprocess`),

  searchTest: (query: string, topK = 5) =>
    api.post('/api/v1/knowledge/search', { query, top_k: topK }),
};