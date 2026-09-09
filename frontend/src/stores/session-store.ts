import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthUser, AuthTokens } from '../types/auth';

interface SessionState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
  setSession: (payload: { user: AuthUser; tokens: AuthTokens }) => void;
  updateAccessToken: (token: string, expiresIn: number) => void;
  clearSession: () => void;
  hydrate: () => void;
}

const defaultOperator: AuthUser = {
  id: 'operator-default',
  email: 'operator@guardianeye.ai',
  full_name: 'GuardianEye Operator',
  is_active: true,
  is_superuser: true,
  role: {
    id: 'role-admin',
    name: 'Admin',
    description: 'System Administrator',
    permissions: '*',
    created_at: new Date().toISOString(),
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      user: defaultOperator,
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      isAuthenticated: true,
      isHydrated: true,
      setSession: ({ user, tokens }) => {
        set({
          user,
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          expiresAt: Date.now() + tokens.expires_in * 1000,
          isAuthenticated: true,
        });
      },
      updateAccessToken: (token: string, expiresIn: number) => {
        set({
          accessToken: token,
          expiresAt: Date.now() + expiresIn * 1000,
          isAuthenticated: true,
        });
      },
      clearSession: () => {
        set({
          user: defaultOperator,
          accessToken: null,
          refreshToken: null,
          expiresAt: null,
          isAuthenticated: true,
        });
      },
      hydrate: () => {
        set({
          isHydrated: true,
          isAuthenticated: true,
        });
      },
    }),

    {
      name: 'guardianeye-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        expiresAt: state.expiresAt,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);

export function isSessionExpired(expiresAt: number | null): boolean {
  if (!expiresAt) {
    return true;
  }

  return Date.now() >= expiresAt;
}
