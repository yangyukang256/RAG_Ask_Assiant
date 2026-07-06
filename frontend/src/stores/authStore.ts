import { create } from 'zustand';
import type { User } from '../types/user';
import { authApi } from '../api/auth';
import { tokenUtils } from '../utils/token';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  loading: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!tokenUtils.getAccessToken(),
  isAdmin: false,
  loading: false,

  login: async (username, password) => {
    const res = await authApi.login({ username, password });
    const { access_token, refresh_token, user } = res.data;
    tokenUtils.setTokens(access_token, refresh_token);
    tokenUtils.setUser(user);
    set({ user, isAuthenticated: true, isAdmin: user.role === 'admin' });
  },

  register: async (username, password, email) => {
    const res = await authApi.register({ username, password, email });
    const { access_token, refresh_token, user } = res.data;
    tokenUtils.setTokens(access_token, refresh_token);
    tokenUtils.setUser(user);
    set({ user, isAuthenticated: true, isAdmin: user.role === 'admin' });
  },

  logout: () => {
    tokenUtils.clearTokens();
    set({ user: null, isAuthenticated: false, isAdmin: false });
  },

  loadUser: async () => {
    const token = tokenUtils.getAccessToken();
    if (!token) return;
    set({ loading: true });
    try {
      const res = await authApi.getMe();
      const user = res.data;
      tokenUtils.setUser(user);
      set({ user, isAuthenticated: true, isAdmin: user.role === 'admin', loading: false });
    } catch {
      tokenUtils.clearTokens();
      set({ user: null, isAuthenticated: false, isAdmin: false, loading: false });
    }
  },
}));