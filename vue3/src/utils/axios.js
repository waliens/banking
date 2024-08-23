// axios.js (for default configuration)
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_PREFIX = 'api';
axios.defaults.baseURL = `${window.location.origin}/${API_PREFIX}`; // connect to same url

axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.request.responseURL.includes('/login') || error.response.request.responseURL.includes('/refresh')) {
      return Promise.reject(error);
    }
    if (error.response.status === 401) {
      const authStore = useAuthStore();
      await authStore.refreshToken();
      error.config.headers['Authorization'] = `Bearer ${authStore.token}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);

export default axios;