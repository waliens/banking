import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useActiveWalletStore } from '../../src/stores/activeWallet'
import { useWalletStore } from '../../src/stores/wallets'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn().mockResolvedValue({}),
  },
}))

import api from '../../src/services/api'

describe('useActiveWalletStore', () => {
  let store
  let walletStore

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useActiveWalletStore()
    walletStore = useWalletStore()
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initialize', () => {
    it('uses default_wallet_id from user preferences', async () => {
      walletStore.wallets = [{ id: 1, name: 'W1', accounts: [] }]
      await store.initialize({ preferences: { default_wallet_id: 1 } })
      expect(store.activeWalletId).toBe(1)
      expect(localStorage.getItem('active_wallet_id')).toBe('1')
    })

    it('falls back to localStorage when no preferences', async () => {
      localStorage.setItem('active_wallet_id', '42')
      await store.initialize({ preferences: {} })
      expect(store.activeWalletId).toBe(42)
    })

    it('auto-selects first wallet when no preference or localStorage', async () => {
      walletStore.wallets = [{ id: 5, name: 'First', accounts: [] }]
      await store.initialize({ preferences: {} })
      expect(store.activeWalletId).toBe(5)
      expect(localStorage.getItem('active_wallet_id')).toBe('5')
    })

    it('fetches wallets if none loaded for auto-select', async () => {
      api.get.mockResolvedValueOnce({ data: [{ id: 10, name: 'Fetched', accounts: [] }] })
      await store.initialize({ preferences: {} })
      expect(api.get).toHaveBeenCalledWith('/wallets')
      expect(store.activeWalletId).toBe(10)
    })
  })

  describe('setActiveWallet', () => {
    it('updates ref, localStorage, and calls API', () => {
      store.setActiveWallet(7)
      expect(store.activeWalletId).toBe(7)
      expect(localStorage.getItem('active_wallet_id')).toBe('7')
      expect(api.put).toHaveBeenCalledWith('/auth/me/preferences', { default_wallet_id: 7 })
    })

    it('clears localStorage when setting null', () => {
      localStorage.setItem('active_wallet_id', '7')
      store.setActiveWallet(null)
      expect(store.activeWalletId).toBeNull()
      expect(localStorage.getItem('active_wallet_id')).toBeNull()
    })
  })

  describe('clear', () => {
    it('resets state and localStorage', () => {
      store.activeWalletId = 5
      localStorage.setItem('active_wallet_id', '5')
      store.clear()
      expect(store.activeWalletId).toBeNull()
      expect(localStorage.getItem('active_wallet_id')).toBeNull()
    })
  })

  describe('computed', () => {
    it('activeWallet returns matching wallet', () => {
      walletStore.wallets = [
        { id: 1, name: 'A', accounts: [] },
        { id: 2, name: 'B', accounts: [{ id_account: 10 }] },
      ]
      store.activeWalletId = 2
      expect(store.activeWallet).toEqual({ id: 2, name: 'B', accounts: [{ id_account: 10 }] })
    })

    it('walletAccountIds extracts account ids', () => {
      walletStore.wallets = [
        { id: 1, name: 'A', accounts: [{ id_account: 10 }, { id_account: 20 }] },
      ]
      store.activeWalletId = 1
      expect(store.walletAccountIds).toEqual([10, 20])
    })
  })
})
