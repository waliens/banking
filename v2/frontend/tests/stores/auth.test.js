import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../src/stores/auth'

// Mock the api module
vi.mock('../../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useAuthStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAuthStore()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with no user', () => {
      expect(store.user).toBeNull()
    })

    it('reads token from localStorage', () => {
      localStorage.setItem('access_token', 'saved-token')
      // re-create store to pick up the stored token
      setActivePinia(createPinia())
      const fresh = useAuthStore()
      expect(fresh.token).toBe('saved-token')
      expect(fresh.isAuthenticated).toBe(true)
    })

    it('isAuthenticated is false when no token', () => {
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('login', () => {
    it('stores token and fetches user on success', async () => {
      api.post.mockResolvedValueOnce({ data: { access_token: 'new-token' } })
      api.get.mockResolvedValueOnce({ data: { id: 1, username: 'alice' } })

      await store.login('alice', 'pass')

      expect(api.post).toHaveBeenCalledWith('/auth/login', { username: 'alice', password: 'pass' })
      expect(store.token).toBe('new-token')
      expect(localStorage.getItem('access_token')).toBe('new-token')
      expect(store.user).toEqual({ id: 1, username: 'alice' })
      expect(store.isAuthenticated).toBe(true)
    })

    it('propagates error on failed login', async () => {
      api.post.mockRejectedValueOnce(new Error('401'))

      await expect(store.login('bad', 'creds')).rejects.toThrow('401')
      expect(store.token).toBeNull()
    })
  })

  describe('fetchUser', () => {
    it('sets user on success', async () => {
      store.token = 'tok'
      api.get.mockResolvedValueOnce({ data: { id: 2, username: 'bob' } })

      await store.fetchUser()

      expect(api.get).toHaveBeenCalledWith('/auth/me')
      expect(store.user).toEqual({ id: 2, username: 'bob' })
    })

    it('clears state on failure', async () => {
      store.token = 'tok'
      store.user = { id: 1 }
      api.get.mockRejectedValueOnce(new Error('401'))

      await store.fetchUser()

      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
    })
  })

  describe('changePassword', () => {
    it('calls PUT /auth/users/:id with new password', async () => {
      store.user = { id: 42, username: 'alice' }
      api.put.mockResolvedValueOnce({})

      await store.changePassword('newpass123')

      expect(api.put).toHaveBeenCalledWith('/auth/users/42', { password: 'newpass123' })
    })

    it('propagates error on failure', async () => {
      store.user = { id: 1, username: 'bob' }
      api.put.mockRejectedValueOnce(new Error('403'))

      await expect(store.changePassword('bad')).rejects.toThrow('403')
    })
  })

  describe('logout', () => {
    it('clears user, token, and localStorage', async () => {
      store.token = 'tok'
      store.user = { id: 1 }
      localStorage.setItem('access_token', 'tok')
      api.post.mockResolvedValueOnce({})

      await store.logout()

      expect(api.post).toHaveBeenCalledWith('/auth/logout')
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('clears state even if logout API fails', async () => {
      store.token = 'tok'
      store.user = { id: 1 }
      api.post.mockRejectedValueOnce(new Error('network'))

      // logout swallows the error via finally, but the rejection still propagates
      try {
        await store.logout()
      } catch {
        // expected
      }

      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
    })
  })
})
