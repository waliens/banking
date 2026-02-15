import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTransactionStore } from '../../src/stores/transactions'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useTransactionStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTransactionStore()
    vi.clearAllMocks()
  })

  describe('fetchTransactions', () => {
    it('fetches list and count in parallel', async () => {
      const txList = [{ id: 1, description: 'Groceries', amount: '42.00' }]
      api.get
        .mockResolvedValueOnce({ data: txList })           // /transactions
        .mockResolvedValueOnce({ data: { count: 1 } })     // /transactions/count

      await store.fetchTransactions({ labeled: true })

      expect(api.get).toHaveBeenCalledTimes(2)
      expect(api.get).toHaveBeenCalledWith('/transactions', { params: { labeled: true } })
      expect(api.get).toHaveBeenCalledWith('/transactions/count', { params: { labeled: true } })
      expect(store.transactions).toEqual(txList)
      expect(store.totalCount).toBe(1)
    })

    it('manages loading flag across both calls', async () => {
      api.get
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: { count: 0 } })

      const promise = store.fetchTransactions()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
    })

    it('resets loading on error', async () => {
      api.get
        .mockRejectedValueOnce(new Error('fail'))
        .mockResolvedValueOnce({ data: { count: 0 } })

      await expect(store.fetchTransactions()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('setCategory', () => {
    it('updates the transaction in-place', async () => {
      store.transactions = [
        { id: 10, description: 'Tx', id_category: null },
      ]
      const updated = { id: 10, description: 'Tx', id_category: 5 }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.setCategory(10, 5)

      expect(api.put).toHaveBeenCalledWith('/transactions/10/category/5')
      expect(result).toEqual(updated)
      expect(store.transactions[0].id_category).toBe(5)
    })
  })

  describe('tagBatch', () => {
    it('sends batch tag request', async () => {
      api.put.mockResolvedValueOnce({})

      const categories = [
        { id_transaction: 1, id_category: 2 },
        { id_transaction: 3, id_category: 4 },
      ]
      await store.tagBatch(categories)

      expect(api.put).toHaveBeenCalledWith('/transactions/tag', { categories })
    })
  })
})
