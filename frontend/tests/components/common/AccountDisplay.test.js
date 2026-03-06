import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AccountDisplay from '../../../src/components/common/AccountDisplay.vue'

describe('AccountDisplay', () => {
  it('renders account name and number', () => {
    const w = mount(AccountDisplay, {
      props: { account: { name: 'Savings', number: 'BE12 3456 7890' } },
    })
    expect(w.text()).toContain('Savings')
    expect(w.text()).toContain('BE12 3456 7890')
  })

  it('shows dashes for null account', () => {
    const w = mount(AccountDisplay, { props: { account: null } })
    expect(w.find('.font-medium').text()).toBe('—')
    expect(w.find('.text-surface-400').text()).toBe('—')
  })

  it('highlights name in primary color when highlight is true', () => {
    const w = mount(AccountDisplay, {
      props: { account: { name: 'Main', number: '123' }, highlight: true },
    })
    expect(w.find('.font-medium').classes()).toContain('text-primary-600')
  })

  it('does not highlight name by default', () => {
    const w = mount(AccountDisplay, {
      props: { account: { name: 'Main', number: '123' } },
    })
    expect(w.find('.font-medium').classes()).not.toContain('text-primary-600')
  })
})
