import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * Testing the api service interceptor logic.
 *
 * Since api.js is a module-level singleton that calls axios.create() at import
 * time, we capture the interceptor callbacks by spying on the real axios
 * instance created inside the module.
 */

// We'll test interceptor logic by importing the real module and
// inspecting / exercising the interceptors it registered.
import api from '../../src/services/api'

describe('api service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('instance config', () => {
    it('has correct baseURL', () => {
      expect(api.defaults.baseURL).toBe('/api/v2')
    })

    it('has withCredentials enabled', () => {
      expect(api.defaults.withCredentials).toBe(true)
    })
  })

  describe('request interceptor', () => {
    it('attaches token from localStorage', () => {
      localStorage.setItem('access_token', 'my-token')

      // Run the request interceptor chain manually
      // axios stores interceptors internally; we can exercise them via
      // the handlers array
      const handlers = api.interceptors.request.handlers
      const fulfilled = handlers.find((h) => h.fulfilled)?.fulfilled

      expect(fulfilled).toBeDefined()

      const config = { headers: {} }
      const result = fulfilled(config)
      expect(result.headers.Authorization).toBe('Bearer my-token')
    })

    it('does not set Authorization when no token', () => {
      localStorage.removeItem('access_token')

      const handlers = api.interceptors.request.handlers
      const fulfilled = handlers.find((h) => h.fulfilled)?.fulfilled

      const config = { headers: {} }
      const result = fulfilled(config)
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('response interceptor', () => {
    let onSuccess, onError

    beforeEach(() => {
      const handlers = api.interceptors.response.handlers
      const handler = handlers.find((h) => h.fulfilled || h.rejected)
      onSuccess = handler?.fulfilled
      onError = handler?.rejected
    })

    it('passes through successful responses', () => {
      const response = { data: 'ok', status: 200 }
      expect(onSuccess(response)).toBe(response)
    })

    it('rejects non-401 errors', async () => {
      const error = { response: { status: 500 }, config: {} }
      await expect(onError(error)).rejects.toBe(error)
    })

    it('attempts refresh on 401', async () => {
      // We can't easily test the full refresh flow without a real HTTP server,
      // but we can verify that a 401 with _retry=false triggers a refresh attempt.
      // The refresh will fail (no server), which exercises the error path.
      const error = {
        response: { status: 401 },
        config: { headers: {}, _retry: false },
      }

      localStorage.setItem('access_token', 'old-token')

      try {
        await onError(error)
      } catch {
        // expected — refresh endpoint not available
      }

      // Token should be cleared after failed refresh
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(window.location.href).toBe('/login')
    })

    it('does not retry if _retry is already set', async () => {
      const error = {
        response: { status: 401 },
        config: { headers: {}, _retry: true },
      }

      await expect(onError(error)).rejects.toBe(error)
    })
  })
})
