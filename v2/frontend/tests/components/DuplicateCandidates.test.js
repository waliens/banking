import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useTransactionStore } from '../../src/stores/transactions'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

import api from '../../src/services/api'
import DuplicateCandidates from '../../src/components/transactions/DuplicateCandidates.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Button: {
    template: '<button @click="$emit(\'click\')">{{ label }}</button>',
    props: ['label', 'severity', 'size'],
  },
}

describe('DuplicateCandidates', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTransactionStore()
    vi.clearAllMocks()
  })

  function mountComponent(transactionId = 5) {
    return mount(DuplicateCandidates, {
      props: { transactionId },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
  }

  it('fetches duplicate candidates on mount', async () => {
    const candidates = [
      { id: 10, date: '2024-06-16', amount: '50.00', description: 'Duplicate', currency: { short_name: 'EUR' } },
    ]
    api.get.mockResolvedValueOnce({ data: candidates })

    mountComponent(5)
    await new Promise((r) => setTimeout(r, 10))

    expect(api.get).toHaveBeenCalledWith('/transactions/5/duplicate_candidates', { params: { days: 7 } })
  })

  it('renders candidate rows', async () => {
    const candidates = [
      { id: 10, date: '2024-06-16', amount: '50.00', description: 'Dup tx', currency: { short_name: 'EUR' } },
    ]
    api.get.mockResolvedValueOnce({ data: candidates })

    const wrapper = mountComponent(5)
    await new Promise((r) => setTimeout(r, 10))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('50.00')
    expect(wrapper.text()).toContain('Dup tx')
  })

  it('shows empty state when no candidates', async () => {
    api.get.mockResolvedValueOnce({ data: [] })

    const wrapper = mountComponent(5)
    await new Promise((r) => setTimeout(r, 10))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('common.noResults')
  })

  it('calls markDuplicate on button click', async () => {
    const candidates = [
      { id: 10, date: '2024-06-16', amount: '50.00', description: 'Dup', currency: { short_name: 'EUR' } },
    ]
    api.get.mockResolvedValueOnce({ data: candidates })
    api.put.mockResolvedValue({ data: { msg: 'success' } })

    const wrapper = mountComponent(5)
    await new Promise((r) => setTimeout(r, 10))
    await wrapper.vm.$nextTick()

    const btn = wrapper.find('button')
    await btn.trigger('click')
    await flushPromises()

    expect(api.put).toHaveBeenCalledWith('/transactions/10/duplicate_of/5')
  })
})
