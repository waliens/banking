import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

vi.mock('../../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../../src/services/api'
import DuplicatesPanel from '../../../src/components/settings/DuplicatesPanel.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  DataTable: {
    template: '<div class="datatable-stub"><slot /></div>',
    props: ['value', 'loading', 'lazy', 'paginator', 'rows', 'totalRecords', 'expandedRows', 'dataKey', 'stripedRows'],
  },
  Column: {
    template: '<div class="column-stub"><slot /></div>',
    props: ['field', 'header', 'expander'],
  },
  Button: {
    template: '<button @click="$emit(\'click\')">{{ label }}</button>',
    props: ['label', 'severity', 'text', 'size'],
  },
  InputText: {
    template: '<input />',
    props: ['modelValue', 'placeholder', 'size'],
  },
  CurrencyDisplay: {
    template: '<span>{{ amount }}</span>',
    props: ['amount', 'currencySymbol', 'showSign', 'colored'],
  },
}

describe('DuplicatesPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // Default: return empty list and count for the fetchTransactions call
    api.get
      .mockResolvedValueOnce({ data: [] })        // /transactions
      .mockResolvedValueOnce({ data: { count: 0 } })  // /transactions/count
  })

  function mountComponent() {
    // Mock useToast since it requires PrimeVue app context
    vi.mock('primevue/usetoast', () => ({
      useToast: () => ({
        add: vi.fn(),
      }),
    }))

    return mount(DuplicatesPanel, {
      global: {
        stubs: stubComponents,
        plugins: [i18n],
      },
    })
  }

  it('renders without error', async () => {
    const wrapper = mountComponent()
    await new Promise((r) => setTimeout(r, 10))

    expect(wrapper.exists()).toBe(true)
  })

  it('shows the duplicates heading', async () => {
    const wrapper = mountComponent()
    await new Promise((r) => setTimeout(r, 10))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('settings.duplicateManagement')
  })

  it('shows empty state when no duplicates', async () => {
    const wrapper = mountComponent()
    await new Promise((r) => setTimeout(r, 10))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('settings.noDuplicates')
  })
})
