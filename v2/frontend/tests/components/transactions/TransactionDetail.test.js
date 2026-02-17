import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
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
  },
}

const i18n = createI18n({ legacy: false, locale: 'en', messages })

const stubComponents = {
  Tag: {
    template: '<span>{{ value }}</span>',
    props: ['value', 'severity', 'class'],
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
        currency_symbol: '€',
        effective_amount: null,
        id_source: 1,
        id_dest: 2,
        source_name: 'Checking',
        dest_name: 'Coffee Corp',
        category_name: 'Food',
        is_reviewed: true,
        notes: null,
        data_source: null,
        external_id: null,
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

  it('shows category name', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Food')
  })

  it('shows Uncategorized when no category', () => {
    const wrapper = mountDetail({ category_name: null })
    expect(wrapper.text()).toContain('Uncategorized')
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
