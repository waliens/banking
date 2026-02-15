import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useAccountStore = defineStore('accounts', () => {
  const accounts = ref([])
  const loading = ref(false)

  async function fetchAccounts() {
    loading.value = true
    try {
      const { data } = await api.get('/accounts')
      accounts.value = data
    } finally {
      loading.value = false
    }
  }

  async function updateAccount(id, payload) {
    const { data } = await api.put(`/accounts/${id}`, payload)
    const idx = accounts.value.findIndex((a) => a.id === id)
    if (idx >= 0) accounts.value[idx] = data
    return data
  }

  return { accounts, loading, fetchAccounts, updateAccount }
})
