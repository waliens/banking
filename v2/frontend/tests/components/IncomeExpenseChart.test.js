import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import IncomeExpenseChart from '../../src/components/analytics/IncomeExpenseChart.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Chart: { template: '<canvas />', props: ['type', 'data', 'options'] },
}

describe('IncomeExpenseChart', () => {
  it('renders chart when data is provided', () => {
    const data = {
      items: [
        { year: 2024, month: 3, income: '200', expense: '80', id_currency: 1 },
        { year: 2024, month: 4, income: '150', expense: '120', id_currency: 1 },
      ],
    }

    const wrapper = mount(IncomeExpenseChart, {
      props: { data },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('shows no-data message when data is null', () => {
    const wrapper = mount(IncomeExpenseChart, {
      props: { data: null },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(false)
    expect(wrapper.find('p').exists()).toBe(true)
  })

  it('shows no-data message when items is empty', () => {
    const wrapper = mount(IncomeExpenseChart, {
      props: { data: { items: [] } },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(false)
  })
})
