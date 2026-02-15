import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useWalletStore = defineStore('wallets', () => {
  const wallets = ref([])
  const loading = ref(false)

  async function fetchWallets() {
    loading.value = true
    try {
      const { data } = await api.get('/wallets')
      wallets.value = data
    } finally {
      loading.value = false
    }
  }

  async function createWallet(payload) {
    const { data } = await api.post('/wallets', payload)
    wallets.value.push(data)
    return data
  }

  async function updateWallet(id, payload) {
    const { data } = await api.put(`/wallets/${id}`, payload)
    const idx = wallets.value.findIndex((w) => w.id === id)
    if (idx >= 0) wallets.value[idx] = data
    return data
  }

  async function deleteWallet(id) {
    await api.delete(`/wallets/${id}`)
    wallets.value = wallets.value.filter((w) => w.id !== id)
  }

  return { wallets, loading, fetchWallets, createWallet, updateWallet, deleteWallet }
})
