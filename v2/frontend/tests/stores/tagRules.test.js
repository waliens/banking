import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTagRuleStore } from '../../src/stores/tagRules'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useTagRuleStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTagRuleStore()
    vi.clearAllMocks()
  })

  describe('fetchRules', () => {
    it('fetches rules and sets loading', async () => {
      const rules = [{ id: 1, name: 'Rule 1', id_category: 1 }]
      api.get.mockResolvedValueOnce({ data: rules })

      const promise = store.fetchRules()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
      expect(store.rules).toEqual(rules)
      expect(api.get).toHaveBeenCalledWith('/tag-rules')
    })

    it('resets loading on error', async () => {
      api.get.mockRejectedValueOnce(new Error('fail'))

      await expect(store.fetchRules()).rejects.toThrow()
      expect(store.loading).toBe(false)
    })
  })

  describe('createRule', () => {
    it('creates and appends rule', async () => {
      const newRule = { id: 2, name: 'New rule', id_category: 1 }
      api.post.mockResolvedValueOnce({ data: newRule })

      const result = await store.createRule({ name: 'New rule', id_category: 1 })

      expect(api.post).toHaveBeenCalledWith('/tag-rules', { name: 'New rule', id_category: 1 })
      expect(result).toEqual(newRule)
      expect(store.rules).toContainEqual(newRule)
    })
  })

  describe('updateRule', () => {
    it('updates rule in list', async () => {
      store.rules = [{ id: 1, name: 'Old', id_category: 1 }]
      const updated = { id: 1, name: 'Updated', id_category: 1 }
      api.put.mockResolvedValueOnce({ data: updated })

      const result = await store.updateRule(1, { name: 'Updated' })

      expect(api.put).toHaveBeenCalledWith('/tag-rules/1', { name: 'Updated' })
      expect(result).toEqual(updated)
      expect(store.rules[0].name).toBe('Updated')
    })
  })

  describe('deleteRule', () => {
    it('removes rule from list', async () => {
      store.rules = [{ id: 1, name: 'Rule 1' }, { id: 2, name: 'Rule 2' }]
      api.delete.mockResolvedValueOnce({})

      await store.deleteRule(1)

      expect(api.delete).toHaveBeenCalledWith('/tag-rules/1')
      expect(store.rules).toHaveLength(1)
      expect(store.rules[0].id).toBe(2)
    })
  })

  describe('applyRules', () => {
    it('calls apply endpoint and returns count', async () => {
      api.post.mockResolvedValueOnce({ data: { applied_count: 5 } })

      const count = await store.applyRules()

      expect(api.post).toHaveBeenCalledWith('/tag-rules/apply')
      expect(count).toBe(5)
    })
  })
})
