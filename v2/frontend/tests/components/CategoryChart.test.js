import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import CategoryChart from '../../src/components/analytics/CategoryChart.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Chart: { template: '<canvas />', props: ['type', 'data', 'options'] },
}

describe('CategoryChart', () => {
  it('renders chart when data is provided', () => {
    const data = {
      items: [
        { id_category: 1, category_name: 'Food', category_color: '#FF0000', amount: '75', id_currency: 1 },
        { id_category: null, category_name: null, category_color: null, amount: '20', id_currency: 1 },
      ],
    }

    const wrapper = mount(CategoryChart, {
      props: { data },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('shows no-data message when data is null', () => {
    const wrapper = mount(CategoryChart, {
      props: { data: null },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(false)
    expect(wrapper.find('p').exists()).toBe(true)
  })

  it('shows no-data message when items is empty', () => {
    const wrapper = mount(CategoryChart, {
      props: { data: { items: [] } },
      global: { stubs: stubComponents, plugins: [i18n] },
    })

    expect(wrapper.find('canvas').exists()).toBe(false)
  })
})
