import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCategoryStore } from '../../src/stores/categories'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useCategoryStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useCategoryStore()
    vi.clearAllMocks()
  })

  describe('fetchCategories', () => {
    it('loads categories', async () => {
      const cats = [
        { id: 1, name: 'Food', id_parent: null },
        { id: 2, name: 'Groceries', id_parent: 1 },
      ]
      api.get.mockResolvedValueOnce({ data: cats })

      await store.fetchCategories()

      expect(store.categories).toEqual(cats)
      expect(store.loading).toBe(false)
    })
  })

  describe('categoryTree', () => {
    it('builds a tree from flat list', () => {
      store.categories = [
        { id: 1, name: 'Food', id_parent: null },
        { id: 2, name: 'Groceries', id_parent: 1 },
        { id: 3, name: 'Transport', id_parent: null },
      ]

      const tree = store.categoryTree
      expect(tree).toHaveLength(2) // Food and Transport
      const food = tree.find((n) => n.name === 'Food')
      expect(food.children).toHaveLength(1)
      expect(food.children[0].name).toBe('Groceries')
      const transport = tree.find((n) => n.name === 'Transport')
      expect(transport.children).toHaveLength(0)
    })

    it('puts orphaned children at root level', () => {
      store.categories = [
        { id: 5, name: 'Orphan', id_parent: 999 },
      ]

      const tree = store.categoryTree
      expect(tree).toHaveLength(1)
      expect(tree[0].name).toBe('Orphan')
    })
  })

  describe('categoryMap', () => {
    it('builds id->category map', () => {
      store.categories = [
        { id: 1, name: 'Food' },
        { id: 2, name: 'Transport' },
      ]

      expect(store.categoryMap.get(1).name).toBe('Food')
      expect(store.categoryMap.get(2).name).toBe('Transport')
      expect(store.categoryMap.get(999)).toBeUndefined()
    })
  })

  describe('createCategory', () => {
    it('appends new category to list', async () => {
      store.categories = [{ id: 1, name: 'Food' }]
      const newCat = { id: 2, name: 'Transport', color: '#0000FF' }
      api.post.mockResolvedValueOnce({ data: newCat })

      const result = await store.createCategory({ name: 'Transport', color: '#0000FF' })

      expect(api.post).toHaveBeenCalledWith('/categories', { name: 'Transport', color: '#0000FF' })
      expect(result).toEqual(newCat)
      expect(store.categories).toHaveLength(2)
    })
  })

  describe('updateCategory', () => {
    it('replaces category in list', async () => {
      store.categories = [{ id: 1, name: 'Old' }]
      const updated = { id: 1, name: 'New' }
      api.put.mockResolvedValueOnce({ data: updated })

      await store.updateCategory(1, { name: 'New' })

      expect(store.categories[0].name).toBe('New')
    })
  })

  describe('deleteCategory', () => {
    it('removes category from list', async () => {
      store.categories = [
        { id: 1, name: 'Food' },
        { id: 2, name: 'Transport' },
      ]
      api.delete.mockResolvedValueOnce({})

      await store.deleteCategory(1)

      expect(api.delete).toHaveBeenCalledWith('/categories/1')
      expect(store.categories).toHaveLength(1)
      expect(store.categories[0].id).toBe(2)
    })
  })
})
