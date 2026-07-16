import { create } from 'zustand';

import type { Tokens, User } from '../types/api';

type AuthState = {
  tokens: Tokens | null;
  user: User | null;
  setSession: (tokens: Tokens, user?: User) => void;
  setUser: (user: User) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  tokens: null,
  user: null,
  setSession: (tokens, user) => set({ tokens, user: user ?? null }),
  setUser: (user) => set({ user }),
  logout: () => set({ tokens: null, user: null }),
}));
