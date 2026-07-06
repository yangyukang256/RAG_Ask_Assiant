import { create } from 'zustand';
import type { KnowledgeDocument, DocumentDetail, DocumentChunk } from '../types/knowledge';
import { knowledgeApi } from '../api/knowledge';

interface KnowledgeState {
  documents: KnowledgeDocument[];
  currentDoc: DocumentDetail | null;
  chunks: DocumentChunk[];
  loading: boolean;

  loadDocuments: (page?: number, status?: string) => Promise<void>;
  getDocument: (id: number) => Promise<void>;
  deleteDocument: (id: number) => Promise<void>;
  uploadDocument: (file: File, description?: string) => Promise<void>;
  loadChunks: (docId: number, page?: number) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  documents: [],
  currentDoc: null,
  chunks: [],
  loading: false,

  loadDocuments: async (page = 1, status?) => {
    set({ loading: true });
    try {
      const res = await knowledgeApi.listDocuments(page, 20, status);
      set({ documents: res.data.items || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  getDocument: async (id) => {
    const res = await knowledgeApi.getDocument(id);
    set({ currentDoc: res.data });
  },

  deleteDocument: async (id) => {
    await knowledgeApi.deleteDocument(id);
    set((s) => ({ documents: s.documents.filter((d) => d.id !== id) }));
  },

  uploadDocument: async (file, description) => {
    await knowledgeApi.uploadDocument(file, description);
    // Refresh list after upload
    const res = await knowledgeApi.listDocuments();
    set({ documents: res.data.items || [] });
  },

  loadChunks: async (docId, page = 1) => {
    const res = await knowledgeApi.getChunks(docId, page);
    set({ chunks: res.data.items || [] });
  },
}));