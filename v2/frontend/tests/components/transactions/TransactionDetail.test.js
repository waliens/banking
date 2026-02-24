import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

vi.mock('../../../src/services/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: { predictions: [] } })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
  },
}))

import TransactionDetail from '../../../src/components/transactions/TransactionDetail.vue'

const messages = {
  en: {
    transactions: {
      source: 'From',
      dest: 'To',
      category: 'Category',
      uncategorized: 'Uncategorized',
      effectiveAmount: 'Effective amount',
    },
    flow: {
      reviewed: 'Reviewed',
      notReviewed: 'Not reviewed',
    },
    ml: {
      suggestion: 'ML Suggestion',
    },
    import: {
      viewDetails: 'View import details',
    },
  },
}

const i18n = createI18n({ legacy: false, locale: 'en', messages })

const stubComponents = {
  Tag: {
    template: '<span>{{ value }}</span>',
    props: ['value', 'severity', 'class'],
  },
  CategorySelect: {
    template: '<div class="category-select-stub"></div>',
    props: ['modelValue', 'placeholder', 'showClear'],
  },
  MLSuggestion: {
    template: '<span class="ml-suggestion">{{ categoryName }}</span>',
    props: ['categoryName', 'categoryColor', 'probability'],
  },
  CurrencyDisplay: {
    template: '<span>{{ amount }} {{ currencySymbol }}</span>',
    props: ['amount', 'currencySymbol', 'colored', 'showSign', 'decimals'],
  },
}

function mountDetail(transaction = {}) {
  return mount(TransactionDetail, {
    props: {
      transaction: {
        id: 1,
        description: 'Coffee Shop',
        date: '2024-06-15',
        amount: '4.50',
        currency: { symbol: '€' },
        effective_amount: null,
        id_source: 1,
        id_dest: 2,
        source: { name: 'Checking', number: 'BE1234', institution: null },
        dest: { name: 'Coffee Corp', number: 'BE5678', institution: null },
        category_name: 'Food',
        id_category: 5,
        is_reviewed: true,
        notes: null,
        data_source: null,
        external_id: null,
        id_import: null,
        id_duplicate_of: null,
        raw_metadata: null,
        ...transaction,
      },
    },
    global: {
      plugins: [i18n],
      stubs: stubComponents,
    },
  })
}

describe('TransactionDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('displays amount and currency', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('4.50')
    expect(wrapper.text()).toContain('€')
  })

  it('displays description and date', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Coffee Shop')
    expect(wrapper.text()).toContain('2024-06-15')
  })

  it('shows effective_amount when different from amount', () => {
    const wrapper = mountDetail({ effective_amount: '3.00' })
    expect(wrapper.text()).toContain('Effective amount')
    expect(wrapper.text()).toContain('3.00')
  })

  it('does not show effective_amount when same as amount', () => {
    const wrapper = mountDetail({ effective_amount: '4.50' })
    expect(wrapper.text()).not.toContain('Effective amount')
  })

  it('shows source and dest account names', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Checking')
    expect(wrapper.text()).toContain('Coffee Corp')
  })

  it('renders a category CategorySelect dropdown', () => {
    const wrapper = mountDetail()
    expect(wrapper.find('.category-select-stub').exists()).toBe(true)
  })

  it('shows notes when present', () => {
    const wrapper = mountDetail({ notes: 'Birthday treat' })
    expect(wrapper.text()).toContain('Birthday treat')
  })

  it('shows reviewed status', () => {
    const wrapper = mountDetail({ is_reviewed: true })
    expect(wrapper.text()).toContain('Reviewed')
  })

  it('shows not reviewed status', () => {
    const wrapper = mountDetail({ is_reviewed: false })
    expect(wrapper.text()).toContain('Not reviewed')
  })
})
