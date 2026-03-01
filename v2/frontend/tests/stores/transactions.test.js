import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTransactionStore } from '../../src/stores/transactions'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
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

      await store.tagBatch({ 1: 2, 3: 4 })

      expect(api.put).toHaveBeenCalledWith('/transactions/tag', {
        categories: [
          { id_transaction: 1, id_category: 2 },
          { id_transaction: 3, id_category: 4 },
        ],
      })
    })
  })

  describe('reviewTransaction', () => {
    it('calls PUT and updates transaction in store', async () => {
      store.transactions = [{ id: 7, is_reviewed: false }]
      const updated = { id: 7, is_reviewed: true }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.reviewTransaction(7)

      expect(api.put).toHaveBeenCalledWith('/transactions/7/review')
      expect(result).toEqual(updated)
      expect(store.transactions[0].is_reviewed).toBe(true)
    })
  })

  describe('reviewBatch', () => {
    it('sends batch review request with transaction IDs', async () => {
      api.put.mockResolvedValueOnce({ data: { msg: 'success', count: 3 } })

      const result = await store.reviewBatch([1, 2, 3])

      expect(api.put).toHaveBeenCalledWith('/transactions/review-batch', { transaction_ids: [1, 2, 3] })
      expect(result).toEqual({ msg: 'success', count: 3 })
    })
  })

  describe('fetchReviewCount', () => {
    it('fetches and sets reviewCount', async () => {
      api.get.mockResolvedValueOnce({ data: { count: 42 } })

      const count = await store.fetchReviewCount()

      expect(api.get).toHaveBeenCalledWith('/transactions/review-inbox/count')
      expect(store.reviewCount).toBe(42)
      expect(count).toBe(42)
    })
  })

  describe('markDuplicate', () => {
    it('calls PUT with correct path', async () => {
      api.put.mockResolvedValueOnce({ data: { msg: 'success' } })

      await store.markDuplicate(5, 3)

      expect(api.put).toHaveBeenCalledWith('/transactions/5/duplicate_of/3')
    })
  })

  describe('fetchDuplicateCandidates', () => {
    it('fetches candidates with days param', async () => {
      const candidates = [{ id: 10, amount: '50.00' }]
      api.get.mockResolvedValueOnce({ data: candidates })

      const result = await store.fetchDuplicateCandidates(5, 7)

      expect(api.get).toHaveBeenCalledWith('/transactions/5/duplicate_candidates', { params: { days: 7 } })
      expect(result).toEqual(candidates)
    })
  })

  describe('unmarkDuplicate', () => {
    it('calls DELETE with correct path', async () => {
      api.delete.mockResolvedValueOnce({ data: { msg: 'success' } })

      const result = await store.unmarkDuplicate(5)

      expect(api.delete).toHaveBeenCalledWith('/transactions/5/duplicate_of')
      expect(result).toEqual({ msg: 'success' })
    })
  })

  describe('fetchTransaction', () => {
    it('fetches a single transaction by id', async () => {
      const tx = { id: 7, description: 'Groceries', amount: '42.00' }
      api.get.mockResolvedValueOnce({ data: tx })

      const result = await store.fetchTransaction(7)

      expect(api.get).toHaveBeenCalledWith('/transactions/7')
      expect(result).toEqual(tx)
    })
  })
})
