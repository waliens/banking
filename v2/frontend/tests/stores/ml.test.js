import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMLStore } from '../../src/stores/ml'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../../src/services/api'

describe('useMLStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useMLStore()
    vi.clearAllMocks()
  })

  describe('fetchModels', () => {
    it('fetches and sets models', async () => {
      const models = [{ id: 1, filename: 'model.pkl', state: 'valid' }]
      api.get.mockResolvedValueOnce({ data: models })

      const result = await store.fetchModels()

      expect(api.get).toHaveBeenCalledWith('/ml/models')
      expect(store.models).toEqual(models)
      expect(result).toEqual(models)
    })
  })

  describe('trainModel', () => {
    it('trains and prepends model', async () => {
      store.models = [{ id: 1, state: 'invalid' }]
      const response = { model: { id: 2, filename: 'new.pkl', state: 'valid' }, message: 'Training complete' }
      api.post.mockResolvedValueOnce({ data: response })

      const result = await store.trainModel()

      expect(api.post).toHaveBeenCalledWith('/ml/train')
      expect(result).toEqual(response)
      expect(store.models[0].id).toBe(2)
      expect(store.models).toHaveLength(2)
    })
  })

  describe('predictTransactions', () => {
    it('fetches predictions and stores them by transaction id', async () => {
      const predictions = [
        { transaction_id: 10, category_id: 1, category_name: 'Food', category_color: '#FF0000', probability: 0.85 },
        { transaction_id: 20, category_id: 2, category_name: 'Transport', category_color: '#0000FF', probability: 0.72 },
      ]
      api.post.mockResolvedValueOnce({ data: { predictions } })

      const result = await store.predictTransactions([10, 20])

      expect(api.post).toHaveBeenCalledWith('/ml/predict', { transaction_ids: [10, 20] })
      expect(result).toEqual(predictions)
      expect(store.predictions[10].category_name).toBe('Food')
      expect(store.predictions[20].probability).toBe(0.72)
    })

    it('skips empty transaction list', async () => {
      await store.predictTransactions([])

      expect(api.post).not.toHaveBeenCalled()
    })
  })
})
