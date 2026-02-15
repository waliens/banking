import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useCategoryStore = defineStore('categories', () => {
  const categories = ref([])
  const loading = ref(false)

  const categoryTree = computed(() => {
    const map = new Map()
    const roots = []
    categories.value.forEach((c) => map.set(c.id, { ...c, children: [] }))
    map.forEach((node) => {
      if (node.id_parent && map.has(node.id_parent)) {
        map.get(node.id_parent).children.push(node)
      } else {
        roots.push(node)
      }
    })
    return roots
  })

  const categoryMap = computed(() => {
    const map = new Map()
    categories.value.forEach((c) => map.set(c.id, c))
    return map
  })

  async function fetchCategories() {
    loading.value = true
    try {
      const { data } = await api.get('/categories')
      categories.value = data
    } finally {
      loading.value = false
    }
  }

  async function createCategory(payload) {
    const { data } = await api.post('/categories', payload)
    categories.value.push(data)
    return data
  }

  async function updateCategory(id, payload) {
    const { data } = await api.put(`/categories/${id}`, payload)
    const idx = categories.value.findIndex((c) => c.id === id)
    if (idx >= 0) categories.value[idx] = data
    return data
  }

  async function deleteCategory(id) {
    await api.delete(`/categories/${id}`)
    categories.value = categories.value.filter((c) => c.id !== id)
  }

  return { categories, categoryTree, categoryMap, loading, fetchCategories, createCategory, updateCategory, deleteCategory }
})
