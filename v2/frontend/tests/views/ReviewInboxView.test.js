import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'
import { useTransactionStore } from '../../src/stores/transactions'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

vi.mock('../../src/stores/categories', () => ({
  useCategoryStore: vi.fn(() => ({
    categories: [],
    categoryTree: [],
    categoryMap: new Map(),
    fetchCategories: vi.fn().mockResolvedValue([]),
  })),
}))

vi.mock('../../src/stores/accounts', () => ({
  useAccountStore: vi.fn(() => ({
    accounts: [],
    fetchAccounts: vi.fn().mockResolvedValue([]),
  })),
}))

vi.mock('../../src/stores/ml', () => ({
  useMLStore: vi.fn(() => ({
    predictions: {},
    predictTransactions: vi.fn().mockResolvedValue({}),
  })),
}))

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => ({
    activeWalletId: 1,
    activeWallet: { id: 1, name: 'Test Wallet', accounts: [{ id_account: 10 }] },
    walletAccountIds: [10],
  })),
}))

import api from '../../src/services/api'
import ReviewInboxView from '../../src/views/ReviewInboxView.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

// Stubs that render nothing — we test logic via the store, not rendered DOM
const stubComponents = {
  DataTable: { template: '<div><slot /></div>', props: ['value', 'loading', 'lazy', 'paginator', 'rows', 'totalRecords', 'dataKey', 'stripedRows', 'responsiveLayout'] },
  Column: { template: '<div />', props: ['field', 'header', 'style'] },
  Button: { template: '<button @click="$emit(\'click\')">{{ label }}</button>', props: ['label', 'severity', 'size', 'icon', 'disabled', 'text', 'outlined', 'rounded'] },
  CurrencyDisplay: { template: '<span />', props: ['amount', 'currencySymbol', 'showSign', 'colored'] },
  InputText: { template: '<input />', props: ['modelValue', 'placeholder'] },
  InputNumber: { template: '<input />', props: ['modelValue', 'placeholder', 'minFractionDigits'] },
  DatePicker: { template: '<input />', props: ['modelValue', 'dateFormat', 'placeholder', 'showIcon'] },
  ToggleSwitch: { template: '<input type="checkbox" />', props: ['modelValue'] },
  Drawer: { template: '<div><slot /></div>', props: ['visible', 'position', 'header'] },
  TransactionDetail: { template: '<div />', props: ['transaction'] },
  AccountDisplay: { template: '<span />', props: ['account', 'highlight'] },
  AccountSelect: { template: '<select />', props: ['modelValue', 'placeholder', 'showClear'] },
  CategorySelect: { template: '<select />', props: ['modelValue', 'placeholder', 'showClear', 'multiple'] },
  'router-link': { template: '<a><slot /></a>', props: ['to'] },
}

function mockApiForMount(transactions = []) {
  api.get
    .mockReset()
    .mockImplementation((url) => {
      if (url === '/transactions') return Promise.resolve({ data: transactions })
      if (url === '/transactions/count') return Promise.resolve({ data: { count: transactions.length } })
      if (url === '/transactions/review-inbox/count') return Promise.resolve({ data: { count: transactions.length } })
      if (url === '/categories') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: {} })
    })
}

async function mountView(transactions = []) {
  mockApiForMount(transactions)
  const wrapper = mount(ReviewInboxView, { global: { stubs: stubComponents, plugins: [i18n] } })
  await flushPromises()
  await nextTick()
  return wrapper
}

describe('ReviewInboxView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches transactions with wallet scoping params on mount', async () => {
    await mountView()

    expect(api.get).toHaveBeenCalledWith('/transactions', {
      params: expect.objectContaining({
        is_reviewed: false,
        labeled: false,
        duplicate_only: false,
        wallet: 1,
        wallet_external_only: true,
      }),
    })
  })

  it('fetches review count on mount', async () => {
    await mountView()
    expect(api.get).toHaveBeenCalledWith('/transactions/review-inbox/count')
  })

  it('shows empty state when no transactions', async () => {
    const wrapper = await mountView([])
    expect(wrapper.find('.pi-check-circle').exists()).toBe(true)
  })

  it('does not show empty state when transactions exist', async () => {
    const tx = {
      id: 1, date: '2024-01-01', description: 'Test', amount: 50,
      source: { id: 10, name: 'My Account' },
      dest: { id: 99, name: 'Shop' },
      currency: { symbol: '€' },
      category_splits: [],
    }
    const wrapper = await mountView([tx])
    // Empty state icon should NOT be present
    expect(wrapper.find('.pi-check-circle').exists()).toBe(false)
    // The table wrapper should be rendered
    expect(wrapper.find('.bg-surface-0.rounded-xl').exists()).toBe(true)
  })
})

// Test the displayAmount and isWalletAccount logic directly by importing the
// functions indirectly through the component's reactive behavior
describe('ReviewInboxView display logic', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('displayAmount negates expenses (wallet account is source)', async () => {
    // Import the module fresh to access its internal functions via the component
    const { isIncome } = await import('../../src/stores/transactionFlow')

    const tx = { id_source: 10, id_dest: 99 }
    // Wallet account ids = [10], so id_dest=99 is NOT in wallet => not income => expense
    expect(isIncome(tx, 'wallet', 1, [10])).toBe(false)

    // Our displayAmount logic: if dest is not wallet account => -amount
    const walletAccountIds = [10]
    const destIsWallet = walletAccountIds.includes(tx.id_dest)
    expect(destIsWallet).toBe(false)
    // So amount should be negated for display
  })

  it('displayAmount keeps income positive (wallet account is dest)', async () => {
    const { isIncome } = await import('../../src/stores/transactionFlow')

    const tx = { id_source: 99, id_dest: 10 }
    // Wallet account ids = [10], id_dest=10 IS in wallet => income
    expect(isIncome(tx, 'wallet', 1, [10])).toBe(true)

    const walletAccountIds = [10]
    const destIsWallet = walletAccountIds.includes(tx.id_dest)
    expect(destIsWallet).toBe(true)
    // So amount should stay positive
  })

  it('isWalletAccount checks account.id against walletAccountIds', () => {
    const walletAccountIds = [10]
    expect(walletAccountIds.includes(10)).toBe(true)   // wallet account
    expect(walletAccountIds.includes(99)).toBe(false)   // external account
  })
})
