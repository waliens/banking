import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import TransactionGroupDialog from '../../src/components/transactions/TransactionGroupDialog.vue'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Dialog: {
    template: '<div v-if="visible"><slot /></div>',
    props: ['visible', 'header', 'modal', 'style', 'closable'],
  },
  InputText: {
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'placeholder', 'class'],
  },
  Button: {
    template: '<button @click="$emit(\'click\')">{{ label }}</button>',
    props: ['label', 'icon', 'severity', 'text', 'size', 'disabled', 'ariaLabel'],
  },
}

describe('TransactionGroupDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function mountComponent(props = {}) {
    return mount(TransactionGroupDialog, {
      props: {
        visible: true,
        group: null,
        initialTransaction: null,
        ...props,
      },
      global: {
        stubs: stubComponents,
        plugins: [createPinia(), i18n],
      },
    })
  }

  it('renders with initial transaction', async () => {
    const tx = {
      id: 1,
      description: 'Dinner',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 1,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Dinner')
  })

  it('shows summary panel with computed totals', async () => {
    const tx = {
      id: 1,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 1,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('100.00')
  })

  it('has linked transactions from initialTransaction prop', async () => {
    const tx = {
      id: 42,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 1,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.linkedTransactions).toHaveLength(1)
    expect(wrapper.vm.linkedTransactions[0].id).toBe(42)
  })
})
