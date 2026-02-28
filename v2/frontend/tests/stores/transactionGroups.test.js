import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTransactionGroupStore } from '../../src/stores/transactionGroups'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useTransactionGroupStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTransactionGroupStore()
    vi.clearAllMocks()
  })

  describe('fetchGroups', () => {
    it('populates state', async () => {
      const groups = [
        { id: 1, name: 'Dinner', transactions: [], total_paid: '100', total_reimbursed: '75', net_expense: '25' },
      ]
      api.get.mockResolvedValueOnce({ data: groups })

      await store.fetchGroups(5)

      expect(api.get).toHaveBeenCalledWith('/transaction-groups', { params: { wallet_id: 5 } })
      expect(store.groups).toEqual(groups)
      expect(store.loading).toBe(false)
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchGroups(5)).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('createGroup', () => {
    it('adds to state', async () => {
      const newGroup = { id: 1, name: 'Dinner', transactions: [], total_paid: '100', total_reimbursed: '75', net_expense: '25' }
      api.post.mockResolvedValueOnce({ data: newGroup })

      const result = await store.createGroup({ name: 'Dinner', transaction_ids: [1, 2] })

      expect(api.post).toHaveBeenCalledWith('/transaction-groups', { name: 'Dinner', transaction_ids: [1, 2] })
      expect(result).toEqual(newGroup)
      expect(store.groups).toHaveLength(1)
    })
  })

  describe('updateGroup', () => {
    it('replaces in state', async () => {
      store.groups = [{ id: 1, name: 'Old' }]
      const updated = { id: 1, name: 'New' }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.updateGroup(1, { name: 'New' })

      expect(result).toEqual(updated)
      expect(store.groups[0].name).toBe('New')
    })
  })

  describe('deleteGroup', () => {
    it('removes from state', async () => {
      store.groups = [
        { id: 1, name: 'Keep' },
        { id: 2, name: 'Delete' },
      ]
      api.delete.mockResolvedValueOnce({})

      await store.deleteGroup(2)

      expect(api.delete).toHaveBeenCalledWith('/transaction-groups/2')
      expect(store.groups).toHaveLength(1)
      expect(store.groups[0].id).toBe(1)
    })
  })

  describe('fetchGroup', () => {
    it('returns group data with wallet_id', async () => {
      const group = { id: 1, name: 'Dinner', transactions: [], total_paid: '100', total_reimbursed: '75', net_expense: '25' }
      api.get.mockResolvedValueOnce({ data: group })

      const result = await store.fetchGroup(1, 5)

      expect(api.get).toHaveBeenCalledWith('/transaction-groups/1', { params: { wallet_id: 5 } })
      expect(result).toEqual(group)
    })
  })
})
