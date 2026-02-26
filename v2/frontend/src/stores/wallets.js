import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useWalletStore = defineStore('wallets', () => {
  const wallets = ref([])
  const loading = ref(false)
  const balance = ref(null)
  const incomeExpense = ref(null)
  const perCategory = ref(null)
  const perCategoryExpense = ref(null)
  const perCategoryIncome = ref(null)
  const perCategoryTable = ref(null)

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

  async function fetchBalance(walletId) {
    const { data } = await api.get(`/wallets/${walletId}/stats/balance`)
    balance.value = data
    return data
  }

  async function fetchIncomeExpense(walletId, { year } = {}) {
    const params = {}
    if (year != null) params.year = year
    const { data } = await api.get(`/wallets/${walletId}/stats/income-expense`, { params })
    incomeExpense.value = data
    return data
  }

  async function fetchPerCategory(walletId, { date_from, date_to, income_only } = {}) {
    const params = {}
    if (date_from) params.date_from = date_from
    if (date_to) params.date_to = date_to
    if (income_only != null) params.income_only = income_only
    const { data } = await api.get(`/wallets/${walletId}/stats/per-category`, { params })
    perCategory.value = data
    return data
  }

  async function fetchPerCategoryPie(walletId, { date_from, date_to, income_only, level, id_category } = {}) {
    const params = {}
    if (date_from) params.date_from = date_from
    if (date_to) params.date_to = date_to
    if (income_only != null) params.income_only = income_only
    if (level != null) params.level = level
    if (id_category != null) params.id_category = id_category
    const { data } = await api.get(`/wallets/${walletId}/stats/per-category`, { params })
    if (income_only) {
      perCategoryIncome.value = data
    } else {
      perCategoryExpense.value = data
    }
    return data
  }

  async function fetchPerCategoryTable(walletId, { date_from, date_to, period_bucket, income_only } = {}) {
    const params = {}
    if (date_from) params.date_from = date_from
    if (date_to) params.date_to = date_to
    if (period_bucket) params.period_bucket = period_bucket
    if (income_only != null) params.income_only = income_only
    const { data } = await api.get(`/wallets/${walletId}/stats/per-category`, { params })
    return data
  }

  return {
    wallets,
    loading,
    balance,
    incomeExpense,
    perCategory,
    perCategoryExpense,
    perCategoryIncome,
    perCategoryTable,
    fetchWallets,
    createWallet,
    updateWallet,
    deleteWallet,
    fetchBalance,
    fetchIncomeExpense,
    fetchPerCategory,
    fetchPerCategoryPie,
    fetchPerCategoryTable,
  }
})
