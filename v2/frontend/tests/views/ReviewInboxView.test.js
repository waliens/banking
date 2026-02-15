import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useTransactionStore } from '../../src/stores/transactions'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

vi.mock('../../src/stores/categories', () => ({
  useCategoryStore: vi.fn(() => ({
    categories: [],
    fetchCategories: vi.fn().mockResolvedValue([]),
  })),
}))

import api from '../../src/services/api'
import ReviewInboxView from '../../src/views/ReviewInboxView.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  DataTable: { template: '<div><slot /></div>', props: ['value', 'loading', 'lazy', 'paginator', 'rows', 'totalRecords', 'expandedRows', 'dataKey', 'stripedRows', 'responsiveLayout'] },
  Column: { template: '<div />', props: ['field', 'header', 'expander', 'style'] },
  Select: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'] },
  Button: { template: '<button @click="$emit(\'click\')">{{ label }}</button>', props: ['label', 'severity', 'size', 'icon', 'disabled', 'text'] },
  DuplicateCandidates: { template: '<div />', props: ['transactionId'] },
}

describe('ReviewInboxView', () => {
  let transactionStore

  beforeEach(() => {
    setActivePinia(createPinia())
    transactionStore = useTransactionStore()
    vi.clearAllMocks()

    // Default mock responses for onMounted calls
    api.get
      .mockResolvedValueOnce({ data: [] })           // /transactions
      .mockResolvedValueOnce({ data: { count: 0 } }) // /transactions/count
      .mockResolvedValueOnce({ data: { count: 0 } }) // /transactions/review-inbox/count
  })

  it('fetches transactions with inbox filters on mount', async () => {
    mount(ReviewInboxView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

    expect(api.get).toHaveBeenCalledWith('/transactions', {
      params: expect.objectContaining({
        is_reviewed: false,
        labeled: false,
        duplicate_only: false,
      }),
    })
  })

  it('fetches review count on mount', async () => {
    mount(ReviewInboxView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

    expect(api.get).toHaveBeenCalledWith('/transactions/review-inbox/count')
  })
})
