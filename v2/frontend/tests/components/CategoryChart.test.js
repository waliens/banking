import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import CategoryChart from '../../src/components/analytics/CategoryChart.vue'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url === '/categories') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: { items: [] } })
    }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  wallet: {
    expense: 'Expense', income: 'Income', noData: 'No data',
    periodYear: 'Year', periodMonth: 'Month', periodRange: 'Range',
    level: 'Level', levelCoarse: 'Coarse', levelFine: 'Fine',
    backToParent: 'Back', uncategorized: 'Uncategorized',
    categoriesSelected: '{n} selected', selectAll: 'Select all', deselectAll: 'Deselect all',
  },
  categories: { selectCategory: 'Select category' },
  transactions: { date: 'Date', uncategorized: 'Uncategorized' },
} } })

const stubComponents = {
  Chart: { template: '<canvas />', props: ['type', 'data', 'options'] },
  SelectButton: { template: '<div />', props: ['modelValue', 'options'] },
  Select: { template: '<div />', props: ['modelValue', 'options'] },
  DatePicker: { template: '<div />', props: ['modelValue'] },
  Button: { template: '<button />', props: ['label'] },
}

describe('CategoryChart', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders without errors', () => {
    const wrapper = mount(CategoryChart, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('shows period filter', () => {
    const wrapper = mount(CategoryChart, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    // Should have expense and income titles
    expect(wrapper.text()).toContain('Expense')
    expect(wrapper.text()).toContain('Income')
  })
})
