import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import CategoryTable from '../../../src/components/analytics/CategoryTable.vue'

vi.mock('../../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { items: [] } }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  wallet: {
    noData: 'No data', monthly: 'Monthly', yearly: 'Yearly',
    periodYear: 'Year', periodMonth: 'Month', periodRange: 'Range',
    expandAll: 'Expand all', collapseAll: 'Collapse all',
    hideEmpty: 'Hide empty', total: 'Total', uncategorized: 'Uncategorized',
    categoriesSelected: '{n} selected', selectAll: 'Select all', deselectAll: 'Deselect all',
  },
  categories: { selectCategory: 'Select category' },
  transactions: { category: 'Category', date: 'Date' },
} } })

const stubComponents = {
  SelectButton: { template: '<div />', props: ['modelValue', 'options'] },
  Button: { template: '<button>{{ label }}<slot /></button>', props: ['label', 'icon'] },
  ToggleSwitch: { template: '<input type="checkbox" />', props: ['modelValue'] },
  Select: { template: '<div />', props: ['modelValue', 'options'] },
  DatePicker: { template: '<div />', props: ['modelValue'] },
}

describe('CategoryTable', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders without errors', () => {
    const wrapper = mount(CategoryTable, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows no data message when empty', () => {
    const wrapper = mount(CategoryTable, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.text()).toContain('No data')
  })

  it('shows hide empty toggle', () => {
    const wrapper = mount(CategoryTable, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.text()).toContain('Hide empty')
  })
})
