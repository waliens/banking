// src/store/auth.ts
import axios from 'axios';
import { defineStore } from 'pinia';

interface User {
  username: string;
  // add other user properties here
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
}

interface Credentials {
  username: string;
  password: string;
}

export const useAuthStore = defineStore({
  id: 'auth',
  state: (): AuthState => ({
    token: null,
    refreshToken: null,
    user: null,
  }),
  actions: {
    async login(credentials: Credentials) { 
      const response = await axios.post("api/login", {'password': credentials.password, 'username': credentials.username})
      this.token = response.data.token;
      this.refreshToken = response.data.refreshToken;
      this.user = response.data.user;
    },
    logout() {
      this.token = null;
      this.refreshToken = null;
      this.user = null;
    },
    async doRefreshToken() {
      let {data} = await axios.post(`/api/refresh`, {}, { headers: { 'Authorization': `Bearer ${this.refreshToken}` }});
      this.token = data.token;
    },
  },
});