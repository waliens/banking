import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useTagRuleStore = defineStore('tagRules', () => {
  const rules = ref([])
  const loading = ref(false)

  async function fetchRules() {
    loading.value = true
    try {
      const { data } = await api.get('/tag-rules')
      rules.value = data
    } finally {
      loading.value = false
    }
  }

  async function createRule(payload) {
    const { data } = await api.post('/tag-rules', payload)
    rules.value.push(data)
    return data
  }

  async function updateRule(id, payload) {
    const { data } = await api.put(`/tag-rules/${id}`, payload)
    const idx = rules.value.findIndex((r) => r.id === id)
    if (idx >= 0) rules.value[idx] = data
    return data
  }

  async function deleteRule(id) {
    await api.delete(`/tag-rules/${id}`)
    rules.value = rules.value.filter((r) => r.id !== id)
  }

  async function applyRules() {
    const { data } = await api.post('/tag-rules/apply')
    return data.applied_count
  }

  return {
    rules, loading,
    fetchRules, createRule, updateRule, deleteRule, applyRules,
  }
})
