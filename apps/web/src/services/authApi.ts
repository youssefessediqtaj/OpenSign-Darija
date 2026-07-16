import { apiRequest } from '../lib/api';
import type { Tokens, User } from '../types/api';

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  display_name: string;
  email: string;
  password: string;
  password_confirm: string;
};

export const authApi = {
  login: (payload: LoginPayload) =>
    apiRequest<Tokens>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload: RegisterPayload) =>
    apiRequest<User>('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => apiRequest<User>('/api/v1/auth/me'),
};
