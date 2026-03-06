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

  async function mergeAccounts(idRepr, idAlias) {
    await api.put('/accounts/merge', { id_repr: idRepr, id_alias: idAlias })
  }

  const mergeSuggestions = ref([])

  async function fetchMergeSuggestions() {
    const { data } = await api.get('/accounts/merge-suggestions')
    mergeSuggestions.value = data
    return data
  }

  async function removeAlias(accountId, aliasId, { promote = false } = {}) {
    await api.delete(`/accounts/${accountId}/aliases/${aliasId}`, { params: { promote } })
  }

  async function addAlias(accountId, payload) {
    const { data } = await api.post(`/accounts/${accountId}/aliases`, payload)
    return data
  }

  return {
    accounts, loading, totalCount, mergeSuggestions,
    fetchAccounts, fetchCount, updateAccount, mergeAccounts,
    fetchMergeSuggestions, removeAlias, addAlias,
  }
})
