import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import FlowTransactionCard from '../../../src/components/flow/FlowTransactionCard.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  CurrencyDisplay: {
    template: '<span>{{ showSign && amount > 0 ? "+" : amount < 0 ? "-" : "" }}{{ Math.abs(amount).toFixed(2) }} {{ currencySymbol }}</span>',
    props: ['amount', 'currencySymbol', 'showSign', 'colored', 'decimals'],
  },
}

function mountCard(props = {}) {
  return mount(FlowTransactionCard, {
    props: {
      transaction: {
        id: 1,
        description: 'Groceries',
        amount: '42.50',
        date: '2024-06-15',
        currency: { symbol: '€' },
      },
      direction: 'expense',
      ...props,
    },
    global: {
      plugins: [i18n],
      stubs: stubComponents,
    },
  })
}

describe('FlowTransactionCard', () => {
  it('displays amount, description, and date', () => {
    const wrapper = mountCard()

    expect(wrapper.text()).toContain('Groceries')
    expect(wrapper.text()).toContain('42.50')
    expect(wrapper.text()).toContain('2024-06-15')
  })

  it('income card has green background (desktop)', () => {
    const wrapper = mountCard({ direction: 'income' })
    const card = wrapper.find('.bg-green-50')
    expect(card.exists()).toBe(true)
  })

  it('expense card has red background (desktop)', () => {
    const wrapper = mountCard({ direction: 'expense' })
    const card = wrapper.find('.bg-red-50')
    expect(card.exists()).toBe(true)
  })

  it('mobile income card has green border', () => {
    const wrapper = mountCard({ direction: 'income', mobile: true })
    const card = wrapper.find('.border-green-400')
    expect(card.exists()).toBe(true)
  })

  it('mobile expense card has red border', () => {
    const wrapper = mountCard({ direction: 'expense', mobile: true })
    const card = wrapper.find('.border-red-400')
    expect(card.exists()).toBe(true)
  })

  it('emits select on click', async () => {
    const wrapper = mountCard()

    await wrapper.find('.bg-red-50').trigger('click')

    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0]).toEqual([1])
  })

  it('renders CurrencyDisplay with showSign', () => {
    const wrapper = mountCard({ direction: 'income' })
    expect(wrapper.text()).toContain('+42.50')
  })
})
