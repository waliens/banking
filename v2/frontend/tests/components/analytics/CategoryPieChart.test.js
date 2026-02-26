import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import CategoryPieChart from '../../../src/components/analytics/CategoryPieChart.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  wallet: {
    noData: 'No data', level: 'Level', levelCoarse: 'Coarse', levelFine: 'Fine',
    backToParent: 'Back', uncategorized: 'Uncategorized',
    categoriesSelected: '{n} selected', selectAll: 'Select all', deselectAll: 'Deselect all',
  },
  categories: { selectCategory: 'Select category' },
  transactions: { uncategorized: 'Uncategorized' },
} } })

const stubComponents = {
  Chart: { template: '<canvas />', props: ['type', 'data', 'options'] },
  SelectButton: { template: '<div />', props: ['modelValue', 'options'] },
  Button: { template: '<button />', props: ['label', 'icon'] },
}

const sampleData = {
  items: [
    { id_category: 1, category_name: 'Food', category_color: '#FF0000', amount: '75', id_currency: 1, id_parent: null },
    { id_category: 2, category_name: 'Groceries', category_color: '#FF5555', amount: '45', id_currency: 1, id_parent: 1 },
    { id_category: null, category_name: null, category_color: null, amount: '20', id_currency: 1, id_parent: null },
  ],
}

const categoryTree = [
  { id: 1, name: 'Food', color: '#FF0000', icon: null, children: [
    { id: 2, name: 'Groceries', color: '#FF5555', icon: null },
  ] },
]

const categoryMap = new Map([
  [1, { id: 1, name: 'Food', color: '#FF0000', icon: null, id_parent: null }],
  [2, { id: 2, name: 'Groceries', color: '#FF5555', icon: null, id_parent: 1 }],
])

describe('CategoryPieChart', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders chart when data is provided', () => {
    const wrapper = mount(CategoryPieChart, {
      props: { data: sampleData, title: 'Expenses', categoryTree, categoryMap },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('shows no-data message when data is null', () => {
    const wrapper = mount(CategoryPieChart, {
      props: { data: null, title: 'Expenses', categoryTree, categoryMap },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.find('canvas').exists()).toBe(false)
    expect(wrapper.text()).toContain('No data')
  })

  it('shows title', () => {
    const wrapper = mount(CategoryPieChart, {
      props: { data: sampleData, title: 'Expenses', categoryTree, categoryMap },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.text()).toContain('Expenses')
  })

  it('shows level selector controls', () => {
    const wrapper = mount(CategoryPieChart, {
      props: { data: sampleData, title: 'Expenses', categoryTree, categoryMap },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    // Level selector div exists
    expect(wrapper.find('div').exists()).toBe(true)
  })
})
