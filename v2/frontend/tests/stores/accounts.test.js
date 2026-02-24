import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAccountStore } from '../../src/stores/accounts'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
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
      expect(api.get).toHaveBeenCalledWith('/accounts', { params: {} })
    })

    it('passes pagination params', async () => {
      api.get.mockResolvedValueOnce({ data: [{ id: 1, name: 'A' }] })

      await store.fetchAccounts({ start: 10, count: 20 })

      expect(api.get).toHaveBeenCalledWith('/accounts', { params: { start: 10, count: 20 } })
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchAccounts()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchCount', () => {
    it('fetches total count', async () => {
      api.get.mockResolvedValueOnce({ data: { count: 42 } })

      const result = await store.fetchCount()

      expect(api.get).toHaveBeenCalledWith('/accounts/count')
      expect(store.totalCount).toBe(42)
      expect(result).toBe(42)
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

  describe('fetchMergeSuggestions', () => {
    it('calls GET /accounts/merge-suggestions and stores results', async () => {
      const suggestions = [{ account_a: { id: 1 }, account_b: { id: 2 }, score: 0.8, reason: 'similar_name' }]
      api.get.mockResolvedValueOnce({ data: suggestions })

      await store.fetchMergeSuggestions()

      expect(api.get).toHaveBeenCalledWith('/accounts/merge-suggestions')
      expect(store.mergeSuggestions).toEqual(suggestions)
    })
  })

  describe('removeAlias', () => {
    it('calls DELETE with default promote=false', async () => {
      api.delete.mockResolvedValueOnce({ data: { msg: 'ok' } })

      await store.removeAlias(1, 2)

      expect(api.delete).toHaveBeenCalledWith('/accounts/1/aliases/2', { params: { promote: false } })
    })

    it('calls DELETE with promote=true when specified', async () => {
      api.delete.mockResolvedValueOnce({ data: { msg: 'ok' } })

      await store.removeAlias(1, 2, { promote: true })

      expect(api.delete).toHaveBeenCalledWith('/accounts/1/aliases/2', { params: { promote: true } })
    })
  })

  describe('addAlias', () => {
    it('calls POST and returns created alias', async () => {
      api.post.mockResolvedValueOnce({ data: { id: 3, name: 'X', number: 'Y', id_account: 1 } })

      const result = await store.addAlias(1, { name: 'X', number: 'Y' })

      expect(api.post).toHaveBeenCalledWith('/accounts/1/aliases', { name: 'X', number: 'Y' })
      expect(result.name).toBe('X')
      expect(result.number).toBe('Y')
      expect(result.id_account).toBe(1)
    })
  })
})
