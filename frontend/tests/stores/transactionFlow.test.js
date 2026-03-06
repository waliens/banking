import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTransactionFlowStore, isIncome, collapseGroups } from '../../src/stores/transactionFlow'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useTransactionFlowStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTransactionFlowStore()
    vi.clearAllMocks()
  })

  describe('fetchPage', () => {
    it('appends items (not replace)', async () => {
      const page1 = [{ id: 1, description: 'Tx1', amount: '10.00' }]
      const page2 = [{ id: 2, description: 'Tx2', amount: '20.00' }]

      // First page: list + count
      api.get
        .mockResolvedValueOnce({ data: page1 })
        .mockResolvedValueOnce({ data: { count: 2 } })

      await store.fetchPage({})

      expect(store.items).toHaveLength(1)
      expect(store.items[0].id).toBe(1)
      expect(store.totalCount).toBe(2)

      // Second page: list only (no count call)
      api.get.mockResolvedValueOnce({ data: page2 })

      await store.fetchPage({})

      expect(store.items).toHaveLength(2)
      expect(store.items[1].id).toBe(2)
    })

    it('sets hasMore to false when offset >= total', async () => {
      api.get
        .mockResolvedValueOnce({ data: [{ id: 1 }] })
        .mockResolvedValueOnce({ data: { count: 1 } })

      await store.fetchPage({})

      expect(store.hasMore).toBe(false)
    })

    it('fetches and caches group details for grouped transactions', async () => {
      const tx = { id: 1, id_transaction_group: 99 }
      const group = { id: 99, name: 'Trip', transactions: [tx] }

      api.get
        .mockResolvedValueOnce({ data: [tx] })
        .mockResolvedValueOnce({ data: { count: 1 } })
        .mockResolvedValueOnce({ data: group })

      await store.fetchPage({})

      expect(store.groupCache[99]).toEqual(group)
      expect(api.get).toHaveBeenCalledWith('/transaction-groups/99', { params: { wallet_id: undefined } })
    })

    it('does not refetch already cached groups', async () => {
      store.groupCache = { 99: { id: 99, name: 'Cached' } }

      const tx = { id: 2, id_transaction_group: 99 }
      api.get
        .mockResolvedValueOnce({ data: [tx] })
        .mockResolvedValueOnce({ data: { count: 1 } })

      await store.fetchPage({})

      // Should not have fetched group 99 again
      expect(api.get).not.toHaveBeenCalledWith('/transaction-groups/99')
    })
  })

  describe('reset', () => {
    it('clears state', async () => {
      store.items = [{ id: 1 }]
      store.currentOffset = 50
      store.hasMore = false
      store.totalCount = 100
      store.groupCache = { 1: {} }

      store.reset()

      expect(store.items).toEqual([])
      expect(store.currentOffset).toBe(0)
      expect(store.hasMore).toBe(true)
      expect(store.totalCount).toBe(0)
      expect(store.groupCache).toEqual({})
    })
  })
})

describe('isIncome', () => {
  it('detects income for wallet context', () => {
    const tx = { id_source: 10, id_dest: 5 }
    expect(isIncome(tx, 'wallet', 1, [5, 6])).toBe(true)
  })

  it('detects expense for wallet context', () => {
    const tx = { id_source: 5, id_dest: 10 }
    expect(isIncome(tx, 'wallet', 1, [5, 6])).toBe(false)
  })

  it('detects income for account context', () => {
    const tx = { id_source: 10, id_dest: 5 }
    expect(isIncome(tx, 'account', 5, [])).toBe(true)
  })

  it('detects expense for account context', () => {
    const tx = { id_source: 5, id_dest: 10 }
    expect(isIncome(tx, 'account', 5, [])).toBe(false)
  })
})

describe('collapseGroups', () => {
  it('replaces first grouped transaction with group placeholder', () => {
    const items = [
      { id: 1, id_transaction_group: 10, date: '2024-06-02' },
      { id: 2, id_transaction_group: 10, date: '2024-06-03' },
      { id: 3, id_transaction_group: null, date: '2024-06-04' },
    ]
    const cache = { 10: { id: 10, name: 'Group A', transactions: [
      { id: 1, date: '2024-06-02' },
      { id: 2, date: '2024-06-03' },
    ] } }

    const result = collapseGroups(items, cache)

    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ type: 'group', group: cache[10], date: '2024-06-02' })
    expect(result[1]).toEqual({ type: 'transaction', transaction: items[2], date: '2024-06-04' })
  })

  it('uses earliest transaction date for group placement', () => {
    const items = [
      { id: 1, id_transaction_group: 10, date: '2024-06-05' },
    ]
    const cache = { 10: { id: 10, name: 'Group A', transactions: [
      { id: 1, date: '2024-06-05' },
      { id: 2, date: '2024-06-01' },
    ] } }

    const result = collapseGroups(items, cache)

    expect(result).toHaveLength(1)
    expect(result[0].date).toBe('2024-06-01')
  })

  it('falls back to transaction if group not in cache', () => {
    const items = [{ id: 1, id_transaction_group: 99, date: '2024-06-01' }]

    const result = collapseGroups(items, {})

    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({ type: 'transaction', transaction: items[0], date: '2024-06-01' })
  })

  it('handles ungrouped transactions', () => {
    const items = [
      { id: 1, id_transaction_group: null, date: '2024-06-01' },
      { id: 2, id_transaction_group: null, date: '2024-06-02' },
    ]

    const result = collapseGroups(items, {})

    expect(result).toHaveLength(2)
    expect(result[0].type).toBe('transaction')
    expect(result[0].date).toBe('2024-06-01')
    expect(result[1].type).toBe('transaction')
    expect(result[1].date).toBe('2024-06-02')
  })
})
