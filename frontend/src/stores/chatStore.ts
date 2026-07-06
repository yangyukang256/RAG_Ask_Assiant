import { create } from 'zustand';
import type { ChatSession, Message, SSEEvent } from '../types/chat';
import { chatApi } from '../api/chat';

interface ChatState {
  sessions: ChatSession[];
  messages: Message[];
  isStreaming: boolean;
  streamingText: string;
  sessionLoading: boolean;

  loadSessions: () => Promise<void>;
  createSession: () => Promise<ChatSession>;
  deleteSession: (id: number) => Promise<void>;
  loadMessages: (sessionId: number) => Promise<void>;

  sendMessage: (sessionId: number, content: string) => Promise<void>;
  appendStreamText: (text: string) => void;
  finishStream: (sessionId: number, citations?: unknown[]) => void;
  clearStream: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  messages: [],
  isStreaming: false,
  streamingText: '',
  sessionLoading: false,

  loadSessions: async () => {
    set({ sessionLoading: true });
    try {
      const res = await chatApi.listSessions();
      set({ sessions: res.data.items || [], sessionLoading: false });
    } catch {
      set({ sessionLoading: false });
    }
  },

  createSession: async () => {
    const res = await chatApi.createSession();
    const session = res.data;
    set((s) => ({ sessions: [session, ...s.sessions] }));
    return session;
  },

  deleteSession: async (id) => {
    await chatApi.deleteSession(id);
    set((s) => ({
      sessions: s.sessions.filter((ss) => ss.id !== id),
      messages: s.messages.filter((m) => m.session_id !== id),
    }));
  },

  loadMessages: async (sessionId) => {
    try {
      const res = await chatApi.getMessages(sessionId);
      const msgs = res.data.messages || [];
      set({ messages: msgs.reverse() }); // reverse to show oldest first
    } catch {
      set({ messages: [] });
    }
  },

  sendMessage: async (sessionId, content) => {
    const userMsg: Message = {
      id: Date.now(),
      session_id: sessionId,
      role: 'user',
      content,
      citations: null,
      token_count: 0,
      created_at: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, userMsg], isStreaming: true, streamingText: '' }));

    const token = localStorage.getItem('kb_access_token');
    const response = await fetch(`http://127.0.0.1:8000/api/v1/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      set({ isStreaming: false });
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            if (event.type === 'text' && event.content) {
              get().appendStreamText(event.content);
            } else if (event.type === 'end') {
              get().finishStream(sessionId, event.citations);
            } else if (event.type === 'error') {
              get().clearStream();
            }
          } catch { /* skip malformed */ }
        }
      }
    }
  },

  appendStreamText: (text) => {
    set((s) => ({ streamingText: s.streamingText + text }));
  },

  finishStream: (sessionId, citations) => {
    const text = get().streamingText;
    const assistantMsg: Message = {
      id: Date.now() + 1,
      session_id: sessionId,
      role: 'assistant',
      content: text,
      citations: citations as Message['citations'],
      token_count: 0,
      created_at: new Date().toISOString(),
    };
    set((s) => ({
      messages: [...s.messages, assistantMsg],
      isStreaming: false,
      streamingText: '',
    }));
  },

  clearStream: () => {
    set({ isStreaming: false, streamingText: '' });
  },
}));