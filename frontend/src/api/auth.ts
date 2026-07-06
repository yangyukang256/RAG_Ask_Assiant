import api from './index';
import type { LoginRequest, RegisterRequest, ChangePasswordRequest, AuthTokens } from '../types/user';

export const authApi = {
  login: (data: LoginRequest) => api.post<AuthTokens>('/api/v1/auth/login', data),

  register: (data: RegisterRequest) => api.post<AuthTokens>('/api/v1/auth/register', data),

  refresh: (refreshToken: string) =>
    api.post<AuthTokens>('/api/v1/auth/refresh', { refresh_token: refreshToken }),

  changePassword: (data: ChangePasswordRequest) =>
    api.post('/api/v1/auth/change-password', data),

  getMe: () => api.get('/api/v1/auth/me'),
};