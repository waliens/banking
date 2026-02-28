import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTransactionStore = defineStore('transactions', () => {
  const transactions = ref([])
  const totalCount = ref(0)
  const loading = ref(false)
  const reviewCount = ref(0)

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

  async function reviewTransaction(id) {
    const { data } = await api.put(`/transactions/${id}/review`)
    const idx = transactions.value.findIndex((t) => t.id === id)
    if (idx >= 0) transactions.value[idx] = data
    return data
  }

  async function reviewBatch(ids) {
    const { data } = await api.put('/transactions/review-batch', { transaction_ids: ids })
    return data
  }

  async function fetchReviewCount() {
    const { data } = await api.get('/transactions/review-inbox/count')
    reviewCount.value = data.count
    return data.count
  }

  async function markDuplicate(idDuplicate, idParent) {
    const { data } = await api.put(`/transactions/${idDuplicate}/duplicate_of/${idParent}`)
    return data
  }

  async function fetchDuplicateCandidates(transactionId, days = 7) {
    const { data } = await api.get(`/transactions/${transactionId}/duplicate_candidates`, { params: { days } })
    return data
  }

  async function unmarkDuplicate(id) {
    const { data } = await api.delete(`/transactions/${id}/duplicate_of`)
    return data
  }

  async function fetchTransaction(id) {
    const { data } = await api.get(`/transactions/${id}`)
    return data
  }

  async function setEffectiveAmount(id, amount) {
    const { data } = await api.put(`/transactions/${id}/effective-amount`, { effective_amount: amount })
    return data
  }

  async function setCategorySplits(id, splits) {
    const { data } = await api.put(`/transactions/${id}/category-splits`, { splits })
    return data
  }

  async function clearCategorySplits(id) {
    const { data } = await api.delete(`/transactions/${id}/category-splits`)
    return data
  }

  return {
    transactions, totalCount, loading, reviewCount,
    fetchTransactions, setCategory, tagBatch,
    reviewTransaction, reviewBatch, fetchReviewCount,
    markDuplicate, fetchDuplicateCandidates,
    unmarkDuplicate, fetchTransaction, setEffectiveAmount,
    setCategorySplits, clearCategorySplits,
  }
})
