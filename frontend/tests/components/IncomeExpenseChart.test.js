import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import IncomeExpenseChart from '../../src/components/analytics/IncomeExpenseChart.vue'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { items: [] } }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  wallet: { income: 'Income', expense: 'Expense', noData: 'No data', year: 'Year' },
} } })

const stubComponents = {
  Chart: { template: '<canvas />', props: ['type', 'data', 'options'] },
  Select: { template: '<div />', props: ['modelValue', 'options'] },
}

describe('IncomeExpenseChart', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders with walletId prop', () => {
    const wrapper = mount(IncomeExpenseChart, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('shows year selector', () => {
    const wrapper = mount(IncomeExpenseChart, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.text()).toContain('Year')
  })

  it('shows no-data message when no data loaded', () => {
    const wrapper = mount(IncomeExpenseChart, {
      props: { walletId: 1 },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.text()).toContain('No data')
  })
})
