import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";
import { TOKEN_KEY } from "../api/client";
import type { User } from "../api/types";
export const useAuth = defineStore("auth", () => {
  const user = ref<User | null>(null);
  function logout() {
    sessionStorage.removeItem(TOKEN_KEY);
    user.value = null;
  }
  async function login(no: string, password: string) {
    const data = await api.login(no, password);
    sessionStorage.setItem(TOKEN_KEY, data.access_token);
    user.value = data.user;
  }
  async function restore() {
    if (sessionStorage.getItem(TOKEN_KEY) && !user.value)
      user.value = await api.me();
  }
  return { user, login, logout, restore };
});
