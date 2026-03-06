import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../../../src/services/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../../../src/services/api'
import AccountSelect from '../../../src/components/common/AccountSelect.vue'

const mockAccounts = [
  { id: 1, name: 'Savings', number: 'BE12 3456 7890' },
  { id: 2, name: 'Checking', number: 'BE98 7654 3210' },
  { id: 3, name: 'Joint', number: 'BE55 1111 2222' },
]

// Stub PrimeVue InputText and Teleport
const stubs = {
  InputText: {
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" :placeholder="placeholder" />',
    props: ['modelValue', 'placeholder'],
  },
  Teleport: { template: '<div><slot /></div>' },
}

function mountSelect(props = {}) {
  return mount(AccountSelect, {
    props,
    global: { stubs },
    attachTo: document.body,
  })
}

describe('AccountSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: /accounts returns mock list, /accounts/:id returns the matching account
    api.get.mockImplementation((url, opts) => {
      if (url === '/accounts') {
        return Promise.resolve({ data: mockAccounts })
      }
      const match = url.match(/\/accounts\/(\d+)/)
      if (match) {
        const account = mockAccounts.find(a => a.id === Number(match[1]))
        return Promise.resolve({ data: account })
      }
      return Promise.resolve({ data: [] })
    })
  })

  it('renders with placeholder text', () => {
    const w = mountSelect({ placeholder: 'Pick one' })
    expect(w.text()).toContain('Pick one')
    w.unmount()
  })

  it('shows selected account name when modelValue is set', async () => {
    const w = mountSelect({ modelValue: 1 })
    await flushPromises()
    expect(w.text()).toContain('Savings')
    w.unmount()
  })

  it('opens dropdown on click', async () => {
    const w = mountSelect()
    expect(w.find('[ref="dropdownRef"]').exists() || w.text()).not.toContain('Search')

    // Click trigger button to open
    await w.find('button').trigger('click')
    await flushPromises()

    // Dropdown should now be visible with accounts
    expect(w.text()).toContain('Savings')
    expect(w.text()).toContain('Checking')
    w.unmount()
  })

  it('emits update:modelValue on account selection', async () => {
    const w = mountSelect()

    // Open dropdown
    await w.find('button').trigger('click')
    await flushPromises()

    // Click first account option
    const accountItems = w.findAll('.cursor-pointer')
    // Find the clickable account divs in the dropdown
    const accountDivs = accountItems.filter(el => el.text().includes('Savings'))
    expect(accountDivs.length).toBeGreaterThan(0)
    await accountDivs[0].trigger('click')

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0]).toEqual([1])
    w.unmount()
  })

  it('shows clear button when showClear and value is set', async () => {
    const w = mountSelect({ modelValue: 1, showClear: true })
    await flushPromises()

    // Should have a clear button (pi-times icon)
    const clearBtn = w.find('.pi-times')
    expect(clearBtn.exists()).toBe(true)
    w.unmount()
  })

  it('does not show clear button when showClear is false', async () => {
    const w = mountSelect({ modelValue: 1, showClear: false })
    await flushPromises()

    const clearBtn = w.find('.pi-times')
    expect(clearBtn.exists()).toBe(false)
    w.unmount()
  })

  it('emits null on clear for single select', async () => {
    const w = mountSelect({ modelValue: 1, showClear: true })
    await flushPromises()

    const clearBtn = w.find('.pi-times').element.closest('button')
    await w.find('.pi-times').trigger('click')
    await flushPromises()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0]).toEqual([null])
    w.unmount()
  })
})
