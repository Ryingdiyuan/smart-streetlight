import { defineStore } from "pinia";
import { login as apiLogin } from "@/services/api/authService";
import { clearAuthSession, AUTH_KEY } from "@/lib/http";

export interface AuthUser {
  id: number;
  username: string;
  role: "admin" | "maintainer" | "user";
}

export interface AuthState {
  token: string;
  user: AuthUser | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: "",
    user: null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userRole: (state) => state.user?.role ?? null,
    username: (state) => state.user?.username ?? "",
  },
  actions: {
    restoreSession() {
      try {
        const raw = uni.getStorageSync(AUTH_KEY);
        if (raw) {
          const session = JSON.parse(raw) as {
            token: string;
            user: AuthUser;
          };
          this.token = session.token;
          this.user = session.user;
        }
      } catch {
        this.logout();
      }
    },
    async login(username: string, password: string) {
      const result = await apiLogin({ username, password });
      const session = {
        token: result.access_token,
        user: result.user,
      };
      uni.setStorageSync(AUTH_KEY, JSON.stringify(session));
      this.token = session.token;
      this.user = session.user;
    },
    logout() {
      clearAuthSession();
      this.token = "";
      this.user = null;
      uni.reLaunch({ url: "/pages/login/index" });
    },
  },
});
