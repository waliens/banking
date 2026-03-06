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

const stubComponents = {
  CurrencyDisplay: {
    template: '<span>{{ Number(amount).toFixed(2) }}</span>',
    props: ['amount', 'currencySymbol', 'colored', 'showSign', 'decimals'],
  },
}

function mountDetail(group = {}) {
  return mount(TransactionGroupDetail, {
    props: {
      group: {
        id: 1,
        name: 'Trip to Paris',
        total_paid: 200,
        total_reimbursed: 50,
        net_expense: 150,
        transactions: [
          { id: 10, description: 'Hotel', date: '2024-06-10', amount: '200.00', effective_amount: '100.00' },
          { id: 11, description: 'Refund', date: '2024-06-12', amount: '50.00', effective_amount: null },
        ],
        ...group,
      },
    },
    global: {
      plugins: [i18n],
      stubs: stubComponents,
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

  it('shows total paid from API response', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Total paid')
    expect(wrapper.text()).toContain('200.00')
  })

  it('shows total reimbursed from API response', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Total reimbursed')
    expect(wrapper.text()).toContain('50.00')
  })

  it('shows net expense from API response', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Net amount')
    expect(wrapper.text()).toContain('150.00')
  })

  it('uses API-provided totals, not amount signs', () => {
    // All amounts are positive (as backend stores them), but API provides correct totals
    const wrapper = mountDetail({
      total_paid: 100,
      total_reimbursed: 25,
      net_expense: 75,
      transactions: [
        { id: 10, description: 'Payment', date: '2024-06-10', amount: '100.00', effective_amount: '75.00' },
        { id: 11, description: 'Refund', date: '2024-06-12', amount: '25.00', effective_amount: '0.00' },
      ],
    })
    expect(wrapper.text()).toContain('100.00')
    expect(wrapper.text()).toContain('25.00')
    expect(wrapper.text()).toContain('75.00')
  })

  it('lists member transactions', () => {
    const wrapper = mountDetail()
    expect(wrapper.text()).toContain('Hotel')
    expect(wrapper.text()).toContain('Refund')
    expect(wrapper.text()).toContain('2024-06-10')
    expect(wrapper.text()).toContain('2024-06-12')
  })
})
