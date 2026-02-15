import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTransactionStore = defineStore('transactions', () => {
  const transactions = ref([])
  const totalCount = ref(0)
  const loading = ref(false)

  async function fetchTransactions(params = {}) {
    loading.value = true
    try {
      const [listRes, countRes] = await Promise.all([
        api.get('/transactions', { params }),
        api.get('/transactions/count', { params }),
      ])
      transactions.value = listRes.data
      totalCount.value = countRes.data.count
    } finally {
      loading.value = false
    }
  }

  async function setCategory(transactionId, categoryId) {
    const { data } = await api.put(`/transactions/${transactionId}/category/${categoryId}`)
    const idx = transactions.value.findIndex((t) => t.id === transactionId)
    if (idx >= 0) transactions.value[idx] = data
    return data
  }

  async function tagBatch(categories) {
    await api.put('/transactions/tag', { categories })
  }

  return { transactions, totalCount, loading, fetchTransactions, setCategory, tagBatch }
})
