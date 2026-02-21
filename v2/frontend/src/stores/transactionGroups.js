import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTransactionGroupStore = defineStore('transactionGroups', () => {
  const groups = ref([])
  const loading = ref(false)

  async function fetchGroups() {
    loading.value = true
    try {
      const { data } = await api.get('/transaction-groups')
      groups.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchGroup(id) {
    const { data } = await api.get(`/transaction-groups/${id}`)
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

  return {
    groups,
    loading,
    fetchGroups,
    fetchGroup,
    createGroup,
    updateGroup,
    deleteGroup,
  }
})
