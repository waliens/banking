import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAccountStore } from '../../src/stores/accounts'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useAccountStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAccountStore()
    vi.clearAllMocks()
  })

  describe('fetchAccounts', () => {
    it('loads accounts and sets loading flag', async () => {
      const accounts = [
        { id: 1, name: 'Checking', number: 'BE1234' },
        { id: 2, name: 'Savings', number: 'BE5678' },
      ]
      api.get.mockResolvedValueOnce({ data: accounts })

      const promise = store.fetchAccounts()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
      expect(store.accounts).toEqual(accounts)
      expect(api.get).toHaveBeenCalledWith('/accounts')
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchAccounts()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('updateAccount', () => {
    it('updates account in-place', async () => {
      store.accounts = [
        { id: 1, name: 'Old', number: 'BE1234' },
        { id: 2, name: 'Other', number: 'BE5678' },
      ]
      const updated = { id: 1, name: 'New', number: 'BE1234' }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.updateAccount(1, { name: 'New' })

      expect(api.put).toHaveBeenCalledWith('/accounts/1', { name: 'New' })
      expect(result).toEqual(updated)
      expect(store.accounts[0].name).toBe('New')
      expect(store.accounts[1].name).toBe('Other') // untouched
    })

    it('handles account not in local list gracefully', async () => {
      store.accounts = []
      const updated = { id: 99, name: 'Ghost' }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.updateAccount(99, { name: 'Ghost' })
      expect(result).toEqual(updated)
      // no crash, accounts unchanged
      expect(store.accounts).toEqual([])
    })
  })
})
