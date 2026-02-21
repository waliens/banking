import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTransactionFlowStore = defineStore('transactionFlow', () => {
  const items = ref([])
  const loading = ref(false)
  const hasMore = ref(true)
  const totalCount = ref(0)
  const currentOffset = ref(0)
  const groupCache = ref({})

  const PAGE_SIZE = 50

  async function fetchPage(params = {}) {
    if (loading.value || !hasMore.value) return
    loading.value = true
    try {
      const queryParams = {
        ...params,
        start: currentOffset.value,
        count: PAGE_SIZE,
        sort_by: 'when',
        order: 'desc',
      }

      const requests = [api.get('/transactions', { params: queryParams })]
      if (currentOffset.value === 0) {
        requests.push(api.get('/transactions/count', { params }))
      }

      const results = await Promise.all(requests)
      const newItems = results[0].data

      if (results.length > 1) {
        totalCount.value = results[1].data.count
      }

      items.value = [...items.value, ...newItems]
      currentOffset.value += newItems.length
      hasMore.value = currentOffset.value < totalCount.value

      // Fetch uncached group details
      const uncachedGroupIds = [
        ...new Set(
          newItems
            .filter((tx) => tx.id_transaction_group && !groupCache.value[tx.id_transaction_group])
            .map((tx) => tx.id_transaction_group),
        ),
      ]
      if (uncachedGroupIds.length > 0) {
        const groupResults = await Promise.all(
          uncachedGroupIds.map((id) => api.get(`/transaction-groups/${id}`)),
        )
        const newCache = { ...groupCache.value }
        groupResults.forEach((res) => {
          newCache[res.data.id] = res.data
        })
        groupCache.value = newCache
      }
    } finally {
      loading.value = false
    }
  }

  function reset() {
    items.value = []
    loading.value = false
    hasMore.value = true
    totalCount.value = 0
    currentOffset.value = 0
    groupCache.value = {}
  }

  return {
    items,
    loading,
    hasMore,
    totalCount,
    currentOffset,
    groupCache,
    fetchPage,
    reset,
  }
})

export function isIncome(tx, contextType, contextId, walletAccountIds) {
  if (contextType === 'wallet') {
    return walletAccountIds.includes(tx.id_dest)
  }
  return tx.id_dest === contextId
}

export function collapseGroups(items, groupCache) {
  const seenGroups = new Set()
  const result = []

  for (const tx of items) {
    if (tx.id_transaction_group) {
      if (seenGroups.has(tx.id_transaction_group)) continue
      seenGroups.add(tx.id_transaction_group)
      const group = groupCache[tx.id_transaction_group]
      if (group) {
        result.push({ type: 'group', group })
      } else {
        result.push({ type: 'transaction', transaction: tx })
      }
    } else {
      result.push({ type: 'transaction', transaction: tx })
    }
  }

  return result
}
