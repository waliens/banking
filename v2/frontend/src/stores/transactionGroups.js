import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTransactionGroupStore = defineStore('transactionGroups', () => {
  const groups = ref([])
  const loading = ref(false)

  async function fetchGroups(walletId) {
    loading.value = true
    try {
      const { data } = await api.get('/transaction-groups', { params: { wallet_id: walletId } })
      groups.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchGroup(id, walletId) {
    const { data } = await api.get(`/transaction-groups/${id}`, { params: { wallet_id: walletId } })
    return data
  }

  async function createGroup(payload) {
    const { data } = await api.post('/transaction-groups', payload)
    groups.value.push(data)
    return data
  }

  async function updateGroup(id, payload) {
    const { data } = await api.put(`/transaction-groups/${id}`, payload)
    const idx = groups.value.findIndex((g) => g.id === id)
    if (idx >= 0) groups.value[idx] = data
    return data
  }

  async function deleteGroup(id) {
    await api.delete(`/transaction-groups/${id}`)
    groups.value = groups.value.filter((g) => g.id !== id)
  }

  async function setGroupCategorySplits(groupId, splits, walletId) {
    const { data } = await api.put(
      `/transaction-groups/${groupId}/category-splits`,
      { splits },
      { params: { wallet_id: walletId } },
    )
    return data
  }

  async function clearGroupCategorySplits(groupId, walletId) {
    const { data } = await api.delete(
      `/transaction-groups/${groupId}/category-splits`,
      { params: { wallet_id: walletId } },
    )
    return data
  }

  return {
    groups,
    loading,
    fetchGroups,
    fetchGroup,
    createGroup,
    updateGroup,
    deleteGroup,
    setGroupCategorySplits,
    clearGroupCategorySplits,
  }
})
