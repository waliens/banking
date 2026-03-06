import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useImportStore = defineStore('imports', () => {
  const imports = ref([])
  const currentImport = ref(null)
  const importTransactions = ref([])
  const importDuplicates = ref([])
  const importAutoTagged = ref([])
  const importAccounts = ref([])
  const loading = ref(false)

  async function fetchImports({ start = 0, count = 20 } = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/imports', { params: { start, count } })
      imports.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchImport(id) {
    const { data } = await api.get(`/imports/${id}`)
    currentImport.value = data
    return data
  }

  async function fetchImportTransactions(id, params = {}) {
    const { data } = await api.get(`/imports/${id}/transactions`, { params })
    importTransactions.value = data
    return data
  }

  async function fetchImportDuplicates(id) {
    const { data } = await api.get(`/imports/${id}/transactions`, { params: { duplicate_only: true } })
    importDuplicates.value = data
    return data
  }

  async function fetchImportAutoTagged(id) {
    const { data } = await api.get(`/imports/${id}/transactions`, { params: { auto_tagged_only: true } })
    importAutoTagged.value = data
    return data
  }

  async function fetchImportAccounts(id) {
    const { data } = await api.get(`/imports/${id}/accounts`)
    importAccounts.value = data
    return data
  }

  return {
    imports,
    currentImport,
    importTransactions,
    importDuplicates,
    importAutoTagged,
    importAccounts,
    loading,
    fetchImports,
    fetchImport,
    fetchImportTransactions,
    fetchImportDuplicates,
    fetchImportAutoTagged,
    fetchImportAccounts,
  }
})
