import { defineStore } from "pinia";
import { clearAuthSession, getAuthSession, saveAuthSession } from "@/services/authStorage";
import { login as requestLogin } from "@/services/api/authService";
import type { AuthSession, LoginPayload } from "@/types/models";

interface AuthState {
  session: AuthSession | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    session: getAuthSession(),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.session?.token),
    currentUser: (state) => state.session?.user ?? null,
  },
  actions: {
    restore() {
      this.session = getAuthSession();
    },
    async login(payload: LoginPayload) {
      const result = await requestLogin(payload);
      this.session = {
        token: result.access_token,
        user: result.user,
      };
      saveAuthSession(this.session);
      return this.session;
    },
    logout() {
      clearAuthSession();
      this.session = null;
    },
  },
});
