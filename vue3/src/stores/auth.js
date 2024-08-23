import { defineStore } from 'pinia';
import axios from 'axios';
import UserService from '@/data/services/user_service';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refresh_token: localStorage.getItem('refresh_token') || '',
    user: null,
  }),
  actions: {
    async login(username, password) {
      const user_service = new UserService();
      const {access_token, refresh_token} = await user_service.login(username, password);
      this.token = access_token;
      this.refresh_token = refresh_token;
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      this.user = await user_service.fetch_current_user();
    },
    logout() {
      this.token = '';
      this.refresh_token = '';
      this.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
    },
    async refreshToken() {
      const user_service = new UserService();
      const {access_token} = await user_service.refresh_token(this.refresh_token);
      this.token = access_token;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    },
  },
});