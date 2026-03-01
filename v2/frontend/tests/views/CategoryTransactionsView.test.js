import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({
    query: {
      wallet: '1',
      category: '5',
      date_from: '2024-01-01',
      date_to: '2024-01-31',
      category_name: 'Food',
      period_label: 'January 2024',
    },
  })),
  useRouter: vi.fn(() => ({
    push: mockPush,
  })),
}))

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => ({
    activeWalletId: 1,
    activeWallet: { id: 1, name: 'Test Wallet', accounts: [{ id_account: 10 }] },
    walletAccountIds: [10],
  })),
}))

vi.mock('../../src/composables/useInfiniteScroll', () => ({
  useInfiniteScroll: vi.fn(),
}))

import api from '../../src/services/api'
import { useRoute } from 'vue-router'
import { useInfiniteScroll } from '../../src/composables/useInfiniteScroll'
import CategoryTransactionsView from '../../src/views/CategoryTransactionsView.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      wallet: {
        backToWallet: 'Back to wallet',
        categoryTransactions: 'Transactions for {category}',
      },
      transactions: { title: 'Transactions', uncategorized: 'Uncategorized' },
      flow: { noTransactions: 'No transactions', transactionDetail: 'Transaction detail' },
      common: { loading: 'Loading...' },
    },
  },
})

const stubComponents = {
  Button: {
    template: '<button @click="$emit(\'click\')"><i v-if="icon" :class="icon" /><span v-if="label">{{ label }}</span></button>',
    props: ['label', 'icon', 'text'],
  },
  Drawer: { template: '<div><slot /></div>', props: ['visible', 'position', 'header'] },
  FlowTransactionCard: {
    template: '<div class="flow-tx-card" :data-direction="direction" @click="$emit(\'select\', transaction.id)">{{ transaction.description }}</div>',
    props: ['transaction', 'direction'],
  },
  FlowGroupCard: {
    template: '<div class="flow-group-card" :data-direction="direction" @click="$emit(\'select\', group.id)">Group {{ group.id }}</div>',
    props: ['group', 'direction'],
  },
  FlowDetailPanel: {
    template: '<div class="flow-detail-panel" />',
    props: ['transactionId'],
  },
}

function makeTx(overrides = {}) {
  return {
    id: 1,
    date: '2024-01-15',
    description: 'Grocery Store',
    amount: 50,
    id_source: 10,
    id_dest: 99,
    id_transaction_group: null,
    currency: { symbol: '€' },
    category_splits: [],
    ...overrides,
  }
}

function mockApi(transactions = [], count = null) {
  api.get.mockReset().mockImplementation((url) => {
    if (url === '/transactions') return Promise.resolve({ data: transactions })
    if (url === '/transactions/count')
      return Promise.resolve({ data: { count: count ?? transactions.length } })
    if (url.startsWith('/transaction-groups/')) {
      const id = Number(url.split('/').pop())
      return Promise.resolve({
        data: {
          id,
          net_expense: 30,
          transactions: transactions.filter((tx) => tx.id_transaction_group === id),
        },
      })
    }
    return Promise.resolve({ data: {} })
  })
}

async function mountView(transactions = [], count = null) {
  mockApi(transactions, count)
  const wrapper = mount(CategoryTransactionsView, {
    global: { stubs: stubComponents, plugins: [i18n] },
  })
  await flushPromises()
  await nextTick()
  return wrapper
}

describe('CategoryTransactionsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // Reset route mock to default query params
    useRoute.mockReturnValue({
      query: {
        wallet: '1',
        category: '5',
        date_from: '2024-01-01',
        date_to: '2024-01-31',
        category_name: 'Food',
        period_label: 'January 2024',
      },
    })
  })

  it('fetches transactions based on route query params on mount', async () => {
    await mountView()

    expect(api.get).toHaveBeenCalledWith('/transactions', {
      params: expect.objectContaining({
        start: 0,
        count: 50,
        order: 'desc',
        wallet: 1,
        wallet_external_only: true,
        category: 5,
        date_from: '2024-01-01',
        date_to: '2024-01-31',
      }),
    })
    expect(api.get).toHaveBeenCalledWith('/transactions/count', {
      params: expect.objectContaining({
        wallet: 1,
        category: 5,
      }),
    })
  })

  it('renders category name and period label from query params', async () => {
    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Transactions for Food')
    expect(wrapper.text()).toContain('January 2024')
  })

  it('back button navigates to wallet view with tab=table', async () => {
    const wrapper = await mountView()

    const backButton = wrapper.find('button')
    await backButton.trigger('click')

    expect(mockPush).toHaveBeenCalledWith({ name: 'wallet', query: { tab: 'table' } })
  })

  it('displays transaction cards with correct expense direction', async () => {
    // id_source=10 (wallet account), id_dest=99 (external) => expense
    const tx = makeTx({ id: 1, id_source: 10, id_dest: 99 })
    const wrapper = await mountView([tx])

    const card = wrapper.find('.flow-tx-card')
    expect(card.exists()).toBe(true)
    expect(card.attributes('data-direction')).toBe('expense')
  })

  it('displays transaction cards with correct income direction', async () => {
    // id_source=99 (external), id_dest=10 (wallet account) => income
    const tx = makeTx({ id: 2, id_source: 99, id_dest: 10 })
    const wrapper = await mountView([tx])

    const card = wrapper.find('.flow-tx-card')
    expect(card.exists()).toBe(true)
    expect(card.attributes('data-direction')).toBe('income')
  })

  it('handles empty transaction list gracefully', async () => {
    const wrapper = await mountView([])

    expect(wrapper.find('.flow-tx-card').exists()).toBe(false)
    expect(wrapper.text()).toContain('No transactions')
    expect(wrapper.text()).toContain('0 transactions')
  })

  it('displays group cards for grouped transactions', async () => {
    const tx1 = makeTx({ id: 1, id_transaction_group: 100, id_source: 10, id_dest: 99 })
    const tx2 = makeTx({ id: 2, id_transaction_group: 100, id_source: 99, id_dest: 10 })
    const wrapper = await mountView([tx1, tx2])

    // Should collapse into one group card
    const groupCards = wrapper.findAll('.flow-group-card')
    expect(groupCards).toHaveLength(1)
    // No standalone transaction cards for grouped transactions
    expect(wrapper.findAll('.flow-tx-card')).toHaveLength(0)
  })

  it('registers infinite scroll with loadMore callback', async () => {
    await mountView()

    expect(useInfiniteScroll).toHaveBeenCalledWith(
      expect.anything(), // sentinel ref
      expect.any(Function), // loadMore callback
      expect.objectContaining({ enabled: expect.anything() }),
    )
  })

  it('loads more transactions via the infinite scroll callback', async () => {
    const txs = [makeTx({ id: 1 })]
    // Report total count > initial batch to allow loadMore
    const wrapper = await mountView(txs, 100)

    // Get the loadMore callback that was passed to useInfiniteScroll
    const loadMoreFn = useInfiniteScroll.mock.calls[0][1]

    // Prepare next page response
    const moreTxs = [makeTx({ id: 2, description: 'Second batch' })]
    api.get.mockReset().mockImplementation((url) => {
      if (url === '/transactions') return Promise.resolve({ data: moreTxs })
      return Promise.resolve({ data: {} })
    })

    await loadMoreFn()
    await flushPromises()
    await nextTick()

    // Should have called /transactions with start=1 (offset by initial batch)
    expect(api.get).toHaveBeenCalledWith('/transactions', {
      params: expect.objectContaining({ start: 1 }),
    })
  })

  it('shows total count from the API', async () => {
    const tx = makeTx()
    const wrapper = await mountView([tx], 42)

    expect(wrapper.text()).toContain('42 transactions')
  })

  it('uses "Uncategorized" as default category name when not provided', async () => {
    useRoute.mockReturnValue({
      query: { wallet: '1' },
    })

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Transactions for Uncategorized')
  })
})
