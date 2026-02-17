import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import TransactionGroupDetail from '../../../src/components/transactions/TransactionGroupDetail.vue'

const messages = {
  en: {
    transactions: {
      totalPaid: 'Total paid',
      totalReimbursed: 'Total reimbursed',
    },
    flow: {
      netAmount: 'Net amount',
    },
  },
}

const i18n = createI18n({ legacy: false, locale: 'en', messages })

function mountDetail(group = {}) {
  return mount(TransactionGroupDetail, {
    props: {
      group: {
        id: 1,
        name: 'Trip to Paris',
        transactions: [
          { id: 10, description: 'Hotel', date: '2024-06-10', amount: '-200.00', effective_amount: '-100.00' },
          { id: 11, description: 'Refund', date: '2024-06-12', amount: '50.00', effective_amount: null },
        ],
        ...group,
      },
    },
    global: {
      plugins: [i18n],
    },
  })
}

describe('TransactionGroupDetail', () => {
  it('displays group name', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Trip to Paris')
  })

  it('shows fallback name when no name', () => {
    const wrapper = mountDetail({ name: null })
    expect(wrapper.text()).toContain('Transaction Group #1')
  })

  it('shows total paid', () => {
    const wrapper = mountDetail()
    // -200.00 is the only negative amount, abs = 200
    expect(wrapper.text()).toContain('Total paid')
    expect(wrapper.text()).toContain('200.00')
  })

  it('shows total reimbursed', () => {
    const wrapper = mountDetail()
    // 50.00 is positive
    expect(wrapper.text()).toContain('Total reimbursed')
    expect(wrapper.text()).toContain('50.00')
  })

  it('shows net expense', () => {
    const wrapper = mountDetail()
    // 200 - 50 = 150
    expect(wrapper.text()).toContain('Net amount')
    expect(wrapper.text()).toContain('150.00')
  })

  it('lists member transactions', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Hotel')
    expect(wrapper.text()).toContain('Refund')
    expect(wrapper.text()).toContain('2024-06-10')
    expect(wrapper.text()).toContain('2024-06-12')
  })
})
