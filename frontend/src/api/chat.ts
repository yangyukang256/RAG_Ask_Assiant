import api from './index';
import type { ChatSession, Message } from '../types/chat';

export const chatApi = {
  listSessions: (page = 1, pageSize = 20) =>
    api.get('/api/v1/sessions', { params: { page, page_size: pageSize } }),

  createSession: (title = '新会话') =>
    api.post<ChatSession>('/api/v1/sessions', { title }),

  updateSession: (id: number, data: { title?: string; status?: string }) =>
    api.put<ChatSession>(`/api/v1/sessions/${id}`, data),

  deleteSession: (id: number) =>
    api.delete(`/api/v1/sessions/${id}`),

  getMessages: (sessionId: number, page = 1, pageSize = 50) =>
    api.get(`/api/v1/sessions/${sessionId}/messages`, {
      params: { page, page_size: pageSize },
    }),
};