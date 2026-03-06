import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useImportStore } from '../../src/stores/imports'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useImportStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useImportStore()
    vi.clearAllMocks()
  })

  describe('fetchImports', () => {
    it('loads imports and sets loading flag', async () => {
      const importList = [
        { id: 1, filename: 'export.csv', created_at: '2024-01-01' },
        { id: 2, filename: 'statement.pdf', created_at: '2024-02-01' },
      ]
      api.get.mockResolvedValueOnce({ data: importList })

      const promise = store.fetchImports()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
      expect(store.imports).toEqual(importList)
      expect(api.get).toHaveBeenCalledWith('/imports', { params: { start: 0, count: 20 } })
    })

    it('passes custom pagination params', async () => {
      api.get.mockResolvedValueOnce({ data: [] })

      await store.fetchImports({ start: 10, count: 50 })

      expect(api.get).toHaveBeenCalledWith('/imports', { params: { start: 10, count: 50 } })
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchImports()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchImport', () => {
    it('fetches a single import by id and stores it', async () => {
      const importData = { id: 1, filename: 'export.csv', created_at: '2024-01-01' }
      api.get.mockResolvedValueOnce({ data: importData })

      const result = await store.fetchImport(1)

      expect(api.get).toHaveBeenCalledWith('/imports/1')
      expect(store.currentImport).toEqual(importData)
      expect(result).toEqual(importData)
    })
  })

  describe('fetchImportTransactions', () => {
    it('fetches transactions for an import', async () => {
      const txList = [
        { id: 10, description: 'Groceries', amount: '42.00' },
        { id: 11, description: 'Gas', amount: '55.00' },
      ]
      api.get.mockResolvedValueOnce({ data: txList })

      const result = await store.fetchImportTransactions(1)

      expect(api.get).toHaveBeenCalledWith('/imports/1/transactions', { params: {} })
      expect(store.importTransactions).toEqual(txList)
      expect(result).toEqual(txList)
    })

    it('passes additional params', async () => {
      api.get.mockResolvedValueOnce({ data: [] })

      await store.fetchImportTransactions(1, { start: 0, count: 10 })

      expect(api.get).toHaveBeenCalledWith('/imports/1/transactions', { params: { start: 0, count: 10 } })
    })
  })

  describe('fetchImportAccounts', () => {
    it('fetches accounts for an import', async () => {
      const accountList = [
        { id: 1, name: 'Checking', number: 'BE1234' },
      ]
      api.get.mockResolvedValueOnce({ data: accountList })

      const result = await store.fetchImportAccounts(1)

      expect(api.get).toHaveBeenCalledWith('/imports/1/accounts')
      expect(store.importAccounts).toEqual(accountList)
      expect(result).toEqual(accountList)
    })
  })
})
