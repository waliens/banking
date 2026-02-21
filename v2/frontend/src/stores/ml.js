import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useMLStore = defineStore('ml', () => {
  const models = ref([])
  const predictions = ref({})

  async function fetchModels() {
    const { data } = await api.get('/ml/models')
    models.value = data
    return data
  }

  async function trainModel() {
    const { data } = await api.post('/ml/train')
    models.value.unshift(data.model)
    return data
  }

  async function predictTransactions(transactionIds) {
    if (!transactionIds.length) return
    const { data } = await api.post('/ml/predict', { transaction_ids: transactionIds })
    for (const pred of data.predictions) {
      predictions.value[pred.transaction_id] = pred
    }
    return data.predictions
  }

  return {
    models, predictions,
    fetchModels, trainModel, predictTransactions,
  }
})
