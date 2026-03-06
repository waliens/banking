import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useWalletStore } from './wallets'
import api from '../services/api'

const STORAGE_KEY = 'active_wallet_id'

export const useActiveWalletStore = defineStore('activeWallet', () => {
  const activeWalletId = ref(null)
  const walletStore = useWalletStore()

  const activeWallet = computed(() =>
    walletStore.wallets.find((w) => w.id === activeWalletId.value) || null,
  )

  const walletAccountIds = computed(() =>
    (activeWallet.value?.accounts || []).map((a) => a.id_account ?? a.id),
  )

  async function initialize(user) {
    // 1. From user preferences
    const prefId = user?.preferences?.default_wallet_id
    if (prefId) {
      activeWalletId.value = prefId
      localStorage.setItem(STORAGE_KEY, String(prefId))
      return
    }

    // 2. From localStorage fallback
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      activeWalletId.value = Number(stored)
      return
    }

    // 3. Auto-select first wallet
    if (!walletStore.wallets.length) {
      await walletStore.fetchWallets()
    }
    if (walletStore.wallets.length > 0) {
      activeWalletId.value = walletStore.wallets[0].id
      localStorage.setItem(STORAGE_KEY, String(activeWalletId.value))
    }
  }

  function setActiveWallet(id) {
    activeWalletId.value = id
    if (id != null) {
      localStorage.setItem(STORAGE_KEY, String(id))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
    // Fire-and-forget: persist to backend
    api.put('/auth/me/preferences', { default_wallet_id: id }).catch(() => {})
  }

  function clear() {
    activeWalletId.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    activeWalletId,
    activeWallet,
    walletAccountIds,
    initialize,
    setActiveWallet,
    clear,
  }
})
