import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWalletStore } from '../../src/stores/wallets'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useWalletStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useWalletStore()
    vi.clearAllMocks()
  })

  describe('fetchWallets', () => {
    it('loads wallets and manages loading flag', async () => {
      const wallets = [{ id: 1, name: 'Personal', accounts: [] }]
      api.get.mockResolvedValueOnce({ data: wallets })

      const promise = store.fetchWallets()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
      expect(store.wallets).toEqual(wallets)
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchWallets()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('createWallet', () => {
    it('appends new wallet to list', async () => {
      store.wallets = []
      const newWallet = { id: 1, name: 'Personal', accounts: [{ id_account: 1 }] }
      api.post.mockResolvedValueOnce({ data: newWallet })

      const result = await store.createWallet({ name: 'Personal', accounts: [{ id_account: 1 }] })

      expect(api.post).toHaveBeenCalledWith('/wallets', { name: 'Personal', accounts: [{ id_account: 1 }] })
      expect(result).toEqual(newWallet)
      expect(store.wallets).toHaveLength(1)
    })
  })

  describe('updateWallet', () => {
    it('replaces wallet in list', async () => {
      store.wallets = [{ id: 1, name: 'Old' }]
      const updated = { id: 1, name: 'New' }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.updateWallet(1, { name: 'New' })

      expect(result).toEqual(updated)
      expect(store.wallets[0].name).toBe('New')
    })
  })

  describe('deleteWallet', () => {
    it('removes wallet from list', async () => {
      store.wallets = [
        { id: 1, name: 'Keep' },
        { id: 2, name: 'Delete' },
      ]
      api.delete.mockResolvedValueOnce({})

      await store.deleteWallet(2)

      expect(api.delete).toHaveBeenCalledWith('/wallets/2')
      expect(store.wallets).toHaveLength(1)
      expect(store.wallets[0].id).toBe(1)
    })
  })

  describe('fetchBalance', () => {
    it('fetches balance and stores result', async () => {
      const balanceData = { accounts: [{ id: 1, name: 'Checking', balance: '1000.00', id_currency: 1, currency: { symbol: '€' } }] }
      api.get.mockResolvedValueOnce({ data: balanceData })

      const result = await store.fetchBalance(5)

      expect(api.get).toHaveBeenCalledWith('/wallets/5/stats/balance')
      expect(store.balance).toEqual(balanceData)
      expect(result).toEqual(balanceData)
    })
  })

  describe('fetchIncomeExpense', () => {
    it('fetches income/expense with year param', async () => {
      const ieData = { items: [{ year: 2024, month: 3, income: '200', expense: '80', id_currency: 1 }] }
      api.get.mockResolvedValueOnce({ data: ieData })

      const result = await store.fetchIncomeExpense(5, { year: 2024 })

      expect(api.get).toHaveBeenCalledWith('/wallets/5/stats/income-expense', { params: { year: 2024 } })
      expect(store.incomeExpense).toEqual(ieData)
      expect(result).toEqual(ieData)
    })

    it('fetches without year param', async () => {
      const ieData = { items: [] }
      api.get.mockResolvedValueOnce({ data: ieData })

      await store.fetchIncomeExpense(5)

      expect(api.get).toHaveBeenCalledWith('/wallets/5/stats/income-expense', { params: {} })
    })
  })

  describe('fetchPerCategory', () => {
    it('fetches per-category with all params', async () => {
      const catData = { items: [{ id_category: 1, category_name: 'Food', amount: '75', id_currency: 1 }] }
      api.get.mockResolvedValueOnce({ data: catData })

      const result = await store.fetchPerCategory(5, { date_from: '2024-01-01', date_to: '2024-12-31', income_only: true })

      expect(api.get).toHaveBeenCalledWith('/wallets/5/stats/per-category', {
        params: { date_from: '2024-01-01', date_to: '2024-12-31', income_only: true },
      })
      expect(store.perCategory).toEqual(catData)
      expect(result).toEqual(catData)
    })

    it('fetches with no params', async () => {
      const catData = { items: [] }
      api.get.mockResolvedValueOnce({ data: catData })

      await store.fetchPerCategory(5)

      expect(api.get).toHaveBeenCalledWith('/wallets/5/stats/per-category', { params: {} })
    })
  })
})
