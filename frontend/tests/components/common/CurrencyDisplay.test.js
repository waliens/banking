import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CurrencyDisplay from '../../../src/components/common/CurrencyDisplay.vue'

describe('CurrencyDisplay', () => {
  it('renders formatted amount with decimals', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 1234.5 } })
    expect(w.text()).toContain('1,234.50')
  })

  it('renders currency symbol', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 100, currencySymbol: '$' } })
    expect(w.text()).toContain('100.00')
    expect(w.text()).toContain('$')
  })

  it('applies green class for positive amount when colored', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 50, colored: true } })
    expect(w.find('span').classes()).toContain('text-green-600')
  })

  it('applies red class for negative amount when colored', () => {
    const w = mount(CurrencyDisplay, { props: { amount: -50, colored: true } })
    expect(w.find('span').classes()).toContain('text-red-500')
  })

  it('applies muted class for zero when colored', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 0, colored: true } })
    expect(w.find('span').classes()).toContain('text-surface-400')
  })

  it('does not apply color classes when not colored', () => {
    const w = mount(CurrencyDisplay, { props: { amount: -50, colored: false } })
    const classes = w.find('span').classes()
    expect(classes).not.toContain('text-red-500')
    expect(classes).not.toContain('text-green-600')
  })

  it('shows + sign for positive when showSign is true', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 100, showSign: true } })
    expect(w.text()).toContain('+100.00')
  })

  it('shows - sign for negative when showSign is true', () => {
    const w = mount(CurrencyDisplay, { props: { amount: -100, showSign: true } })
    expect(w.text()).toContain('-100.00')
  })

  it('shows - sign for negative even without showSign', () => {
    const w = mount(CurrencyDisplay, { props: { amount: -100 } })
    expect(w.text()).toContain('-100.00')
  })

  it('respects custom decimals', () => {
    const w = mount(CurrencyDisplay, { props: { amount: 99.999, decimals: 0 } })
    expect(w.text()).toContain('100')
    expect(w.text()).not.toContain('.')
  })

  it('parses string amounts', () => {
    const w = mount(CurrencyDisplay, { props: { amount: '42.10' } })
    expect(w.text()).toContain('42.10')
  })
})
