import { create } from "zustand";
import { persist } from "zustand/middleware";

import { ApiError, getMe, loginUser, registerUser } from "@/lib/api";
import { isUnauthorizedStatus, onUnauthorized } from "@/lib/authSession";
import type { UserResponse } from "@/types/user";

const STORAGE_KEY = "diao-travelagent-auth";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrateFromStorage: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      login: async (username, password) => {
        const response = await loginUser({ username, password });
        set({
          token: response.access_token,
          user: response.user,
        });
      },

      register: async (username, email, password) => {
        const response = await registerUser({ username, email, password });
        set({
          token: response.access_token,
          user: response.user,
        });
      },

      logout: () => {
        set({ token: null, user: null });
        void import("@/stores/chatStore").then(({ useChatStore }) => {
          useChatStore.getState().reset();
        });
      },

      hydrateFromStorage: async () => {
        const { token } = get();
        if (!token) {
          get().logout();
          return;
        }

        try {
          const me = await getMe(token);
          set({ token, user: me });
        } catch (error) {
          if (error instanceof ApiError && isUnauthorizedStatus(error.status)) {
            get().logout();
            return;
          }
          get().logout();
        }
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    },
  ),
);

if (typeof window !== "undefined") {
  onUnauthorized(() => {
    useAuthStore.getState().logout();
  });
}

export function selectIsAuthenticated(state: AuthState): boolean {
  return Boolean(state.token && state.user);
}
