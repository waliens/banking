import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import TransactionGroupDialog from '../../src/components/transactions/TransactionGroupDialog.vue'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import api from '../../src/services/api'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Dialog: {
    template: '<div v-if="visible"><slot /></div>',
    props: ['visible', 'header', 'modal', 'style', 'closable'],
  },
  InputText: {
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'placeholder', 'class', 'size'],
  },
  Button: {
    template: '<button @click="$emit(\'click\')">{{ label }}</button>',
    props: ['label', 'icon', 'severity', 'text', 'size', 'disabled', 'ariaLabel', 'class'],
  },
}

describe('TransactionGroupDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: [] })
  })

  function mountComponent(props = {}) {
    return mount(TransactionGroupDialog, {
      props: {
        visible: true,
        group: null,
        initialTransaction: null,
        walletId: 1,
        walletAccountIds: [10, 20],
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
      id_source: 10,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await flushPromises()

    expect(wrapper.text()).toContain('Dinner')
  })

  it('shows summary panel with computed totals', async () => {
    const tx = {
      id: 1,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 10,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await flushPromises()

    expect(wrapper.text()).toContain('100.00')
  })

  it('has linked transactions from initialTransaction prop', async () => {
    const tx = {
      id: 42,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 10,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    const wrapper = mountComponent({ initialTransaction: tx })
    await flushPromises()

    expect(wrapper.vm.linkedTransactions).toHaveLength(1)
    expect(wrapper.vm.linkedTransactions[0].id).toBe(42)
  })

  it('fetches transactions on open', async () => {
    const tx = {
      id: 1,
      description: 'Test',
      date: '2024-06-15',
      amount: '50.00',
      id_source: 10,
      id_dest: 2,
    }

    mountComponent({ initialTransaction: tx })
    await flushPromises()

    // Should have made 2 API calls: older (date_to = anchor, desc) and newer (date_from > anchor, asc)
    const getCalls = api.get.mock.calls.filter(([url]) => url === '/transactions')
    expect(getCalls.length).toBe(2)
    const params = getCalls.map(([, opts]) => opts.params)
    expect(params.some((p) => p.date_to === '2024-06-15' && p.order === 'desc')).toBe(true)
    expect(params.some((p) => p.date_from === '2024-06-16' && p.order === 'asc')).toBe(true)
  })

  it('uses wallet scoping in API calls', async () => {
    const tx = {
      id: 1,
      description: 'Test',
      date: '2024-06-15',
      amount: '50.00',
      id_source: 10,
      id_dest: 2,
    }

    mountComponent({ initialTransaction: tx, walletId: 7 })
    await flushPromises()

    const getCalls = api.get.mock.calls.filter(([url]) => url === '/transactions')
    expect(getCalls.length).toBeGreaterThan(0)
    expect(getCalls[0][1].params.wallet).toBe(7)
    expect(getCalls[0][1].params.wallet_external_only).toBe(true)
  })

  it('includes wallet_id in save payload', async () => {
    const tx = {
      id: 1,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 10,
      id_dest: 2,
      effective_amount: null,
      id_transaction_group: null,
    }

    api.post.mockResolvedValue({ data: { id: 1, name: null, transactions: [tx], total_paid: 100, total_reimbursed: 0, net_expense: 100, category_splits: [] } })

    const wrapper = mountComponent({ initialTransaction: tx, walletId: 7 })
    await flushPromises()

    // Trigger save
    await wrapper.vm.save()
    await flushPromises()

    expect(api.post).toHaveBeenCalledWith('/transaction-groups', expect.objectContaining({
      wallet_id: 7,
      transaction_ids: [1],
    }))
  })

  it('sends exclude_grouped param in API calls', async () => {
    const tx = {
      id: 1,
      description: 'Test',
      date: '2024-06-15',
      amount: '50.00',
      id_source: 10,
      id_dest: 2,
    }

    mountComponent({ initialTransaction: tx })
    await flushPromises()

    const getCalls = api.get.mock.calls.filter(([url]) => url === '/transactions')
    expect(getCalls.length).toBeGreaterThan(0)
    for (const [, opts] of getCalls) {
      expect(opts.params.exclude_grouped).toBe(true)
    }
  })

  it('determines outgoing based on walletAccountIds', async () => {
    const tx = {
      id: 1,
      description: 'Payment',
      date: '2024-06-01',
      amount: '100.00',
      id_source: 10,  // in walletAccountIds
      id_dest: 99,
    }

    const wrapper = mountComponent({
      initialTransaction: tx,
      walletAccountIds: [10, 20],
    })
    await flushPromises()

    // isOutgoing should be true because id_source (10) is in walletAccountIds
    expect(wrapper.vm.isOutgoing(tx)).toBe(true)

    // A transaction from outside wallet should be incoming
    const incomingTx = { ...tx, id_source: 99, id_dest: 10 }
    expect(wrapper.vm.isOutgoing(incomingTx)).toBe(false)
  })
})
