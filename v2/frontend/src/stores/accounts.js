import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useAccountStore = defineStore('accounts', () => {
  const accounts = ref([])
  const loading = ref(false)
  const totalCount = ref(0)

  async function fetchAccounts({ start, count } = {}) {
    loading.value = true
    try {
      const params = {}
      if (start != null) params.start = start
      if (count != null) params.count = count
      const { data } = await api.get('/accounts', { params })
      accounts.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchCount() {
    const { data } = await api.get('/accounts/count')
    totalCount.value = data.count
    return data.count
  }

  async function updateAccount(id, payload) {
    const { data } = await api.put(`/accounts/${id}`, payload)
    const idx = accounts.value.findIndex((a) => a.id === id)
    if (idx >= 0) accounts.value[idx] = data
    return data
  }

  return { accounts, loading, totalCount, fetchAccounts, fetchCount, updateAccount }
})
