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
    const items = Object.entries(categories).map(([txId, catId]) => ({
      id_transaction: Number(txId),
      id_category: catId,
    }))
    await api.put('/transactions/tag', { categories: items })
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

  // --- Transaction Group review functions ---

  async function fetchUnreviewedGroups(walletId) {
    const { data } = await api.get('/transaction-groups/unreviewed', { params: { wallet_id: walletId } })
    return data
  }

  async function setGroupCategory(groupId, categoryId, walletId) {
    const { data } = await api.put(`/transaction-groups/${groupId}/category/${categoryId}`, null, {
      params: { wallet_id: walletId },
    })
    return data
  }

  async function reviewGroup(groupId, walletId) {
    const { data } = await api.put(`/transaction-groups/${groupId}/review`, null, {
      params: { wallet_id: walletId },
    })
    return data
  }

  async function unreviewUncategorized() {
    const { data } = await api.put('/transactions/unreview-uncategorized')
    return data
  }

  return {
    transactions, totalCount, loading, reviewCount,
    fetchTransactions, setCategory, tagBatch,
    reviewTransaction, reviewBatch, fetchReviewCount,
    markDuplicate, fetchDuplicateCandidates,
    unmarkDuplicate, fetchTransaction, setEffectiveAmount,
    setCategorySplits, clearCategorySplits,
    fetchUnreviewedGroups, setGroupCategory, reviewGroup,
    unreviewUncategorized,
  }
})
