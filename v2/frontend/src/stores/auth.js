import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    await fetchUser()
    // Initialize active wallet after login
    const { useActiveWalletStore } = await import('./activeWallet')
    const activeWalletStore = useActiveWalletStore()
    await activeWalletStore.initialize(user.value)
  }

  async function fetchUser() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      user.value = null
      token.value = null
      localStorage.removeItem('access_token')
    }
  }

  async function changePassword(newPassword) {
    await api.put(`/auth/users/${user.value.id}`, { password: newPassword })
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } finally {
      user.value = null
      token.value = null
      localStorage.removeItem('access_token')
      // Clear active wallet on logout
      const { useActiveWalletStore } = await import('./activeWallet')
      const activeWalletStore = useActiveWalletStore()
      activeWalletStore.clear()
    }
  }

  return { user, token, isAuthenticated, login, fetchUser, changePassword, logout }
})
