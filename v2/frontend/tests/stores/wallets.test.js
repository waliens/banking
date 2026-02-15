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
})
