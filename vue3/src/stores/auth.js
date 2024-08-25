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
    /**
     * Set the access token and update the axios default headers and local storage
     * @param {*} access_token 
     */
    async set_access_token(access_token) {
      this.token = access_token;
      if (access_token) {
        this.token = access_token;
        localStorage.setItem('token', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      } else {
        this.token = '';
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
    },
    /**
     * Set the refresh token and update the local storage
     * @param {*} refresh_token 
     */
    async set_refresh_token(refresh_token) {
      if (refresh_token) {
        this.refresh_token = refresh_token;
        localStorage.setItem('refresh_token', refresh_token);
      } else {
        this.refresh_token = '';
        localStorage.removeItem('refresh_token');
      }
    },
    /**
     * Initialize the store by fetching the current user if the access token is set
     * and setting the user to null if the access token is not set in the local storage
     */
    async init() {
      const access_token = localStorage.getItem('token');
      if (access_token) {
        this.set_access_token(access_token);
        this.set_refresh_token(localStorage.getItem('refresh_token'));
        const user_service = new UserService();
        this.user = await user_service.fetch_current_user();
      } else {
        this.set_access_token(undefined);
        this.set_refresh_token(undefined);
        this.user = null;
      }
    },
    async login(username, password) {
      const user_service = new UserService();
      const {access_token, refresh_token} = await user_service.login(username, password);
      this.set_access_token(access_token);
      this.set_refresh_token(refresh_token);
      this.user = await user_service.fetch_current_user();
    },
    logout() {
      this.set_access_token(undefined);
      this.set_refresh_token(undefined);
      this.user = null;
    },
    async refreshToken() {
      const user_service = new UserService();
      const {access_token} = await user_service.refresh_token(this.refresh_token);
      this.set_access_token(access_token);
    },
  },
});