import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'

// Mock vue-router
const mockRoute = { query: {} }
vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => mockRoute),
}))

// Mock stores
const mockWalletStore = {
  wallets: [{ id: 1, name: 'Main Wallet' }],
  balance: null,
  loading: false,
  fetchWallets: vi.fn().mockResolvedValue([]),
  fetchBalance: vi.fn().mockResolvedValue({}),
}

const mockActiveWalletStore = {
  activeWalletId: 1,
  activeWallet: { id: 1, name: 'Main Wallet', description: 'My wallet' },
  walletAccountIds: [10],
  setActiveWallet: vi.fn(),
}

vi.mock('../../src/stores/wallets', () => ({
  useWalletStore: vi.fn(() => mockWalletStore),
}))

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => mockActiveWalletStore),
}))

import WalletTabView from '../../src/views/WalletTabView.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      nav: { wallet: 'Wallet', import: 'Import' },
      wallet: {
        selectWallet: 'Select a wallet',
        noWalletSelected: 'No wallet selected',
        createFirst: 'Import transactions or select/create a wallet.',
        incomeExpense: 'Income / Expense',
        perCategory: 'Per Category',
        table: 'Table',
        balance: 'Balance',
        noData: 'No data available',
      },
    },
  },
})

const stubComponents = {
  Select: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'] },
  Button: { template: '<button>{{ label }}</button>', props: ['label', 'icon'] },
  Tabs: { template: '<div class="tabs-stub" :data-value="value"><slot /></div>', props: ['value'] },
  TabList: { template: '<div class="tablist-stub"><slot /></div>' },
  Tab: { template: '<div class="tab-stub"><slot /></div>', props: ['value'] },
  TabPanels: { template: '<div class="tabpanels-stub"><slot /></div>' },
  TabPanel: { template: '<div class="tabpanel-stub"><slot /></div>', props: ['value'] },
  IncomeExpenseChart: { template: '<div class="income-expense-chart-stub" />', props: ['walletId'] },
  CategoryChart: { template: '<div class="category-chart-stub" />', props: ['walletId'] },
  CategoryTable: { template: '<div class="category-table-stub" />', props: ['walletId'] },
  CurrencyDisplay: { template: '<span />', props: ['amount', 'currencySymbol'] },
  AccountDisplay: { template: '<span />', props: ['account'] },
  'router-link': { template: '<a :href="to"><slot /></a>', props: ['to'] },
}

function resetMocks() {
  mockRoute.query = {}
  mockWalletStore.wallets = [{ id: 1, name: 'Main Wallet' }]
  mockWalletStore.balance = null
  mockWalletStore.fetchWallets.mockReset().mockResolvedValue([])
  mockWalletStore.fetchBalance.mockReset().mockResolvedValue({})
  mockActiveWalletStore.activeWalletId = 1
  mockActiveWalletStore.activeWallet = { id: 1, name: 'Main Wallet', description: 'My wallet' }
  mockActiveWalletStore.walletAccountIds = [10]
  mockActiveWalletStore.setActiveWallet.mockReset()
}

async function mountView() {
  const wrapper = mount(WalletTabView, {
    global: { stubs: stubComponents, plugins: [i18n] },
  })
  await flushPromises()
  await nextTick()
  return wrapper
}

describe('WalletTabView', () => {
  beforeEach(() => {
    resetMocks()
    vi.clearAllMocks()
  })

  it('renders without errors when wallet is selected', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.tabs-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('Main Wallet')
  })

  it('shows wallet description when available', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('My wallet')
  })

  it('shows "no wallet" message when no active wallet', async () => {
    mockActiveWalletStore.activeWalletId = null
    mockActiveWalletStore.activeWallet = null
    const wrapper = await mountView()

    expect(wrapper.text()).toContain('No wallet selected')
    expect(wrapper.text()).toContain('Import transactions or select/create a wallet.')
    // Tabs should not be rendered
    expect(wrapper.find('.tabs-stub').exists()).toBe(false)
  })

  it('reads initial tab from route query param', async () => {
    mockRoute.query = { tab: 'per-category' }
    const wrapper = await mountView()

    const tabs = wrapper.find('.tabs-stub')
    expect(tabs.exists()).toBe(true)
    expect(tabs.attributes('data-value')).toBe('per-category')
  })

  it('defaults to income-expense tab when no query param', async () => {
    mockRoute.query = {}
    const wrapper = await mountView()

    const tabs = wrapper.find('.tabs-stub')
    expect(tabs.attributes('data-value')).toBe('income-expense')
  })

  it('renders all four tab panels', async () => {
    const wrapper = await mountView()

    const tabs = wrapper.findAll('.tab-stub')
    expect(tabs).toHaveLength(4)
    expect(tabs[0].text()).toContain('Income / Expense')
    expect(tabs[1].text()).toContain('Per Category')
    expect(tabs[2].text()).toContain('Table')
    expect(tabs[3].text()).toContain('Balance')
  })

  it('renders IncomeExpenseChart, CategoryChart, and CategoryTable stubs', async () => {
    const wrapper = await mountView()

    expect(wrapper.find('.income-expense-chart-stub').exists()).toBe(true)
    expect(wrapper.find('.category-chart-stub').exists()).toBe(true)
    expect(wrapper.find('.category-table-stub').exists()).toBe(true)
  })

  it('fetches balance on mount when wallet is selected', async () => {
    await mountView()
    expect(mockWalletStore.fetchBalance).toHaveBeenCalledWith(1)
  })

  it('does not fetch balance when no wallet is selected', async () => {
    mockActiveWalletStore.activeWalletId = null
    mockActiveWalletStore.activeWallet = null
    await mountView()
    expect(mockWalletStore.fetchBalance).not.toHaveBeenCalled()
  })

  it('does not fetch wallets if already loaded', async () => {
    mockWalletStore.wallets = [{ id: 1, name: 'Main Wallet' }]
    await mountView()
    expect(mockWalletStore.fetchWallets).not.toHaveBeenCalled()
  })

  it('fetches wallets on mount if none loaded', async () => {
    mockWalletStore.wallets = []
    await mountView()
    expect(mockWalletStore.fetchWallets).toHaveBeenCalled()
  })

  it('renders balance accounts when balance data exists', async () => {
    mockWalletStore.balance = {
      accounts: [
        { id: 10, name: 'Checking', balance: 1500.50, currency_symbol: 'EUR' },
        { id: 11, name: 'Savings', balance: 3000, currency_symbol: 'EUR' },
      ],
    }
    const wrapper = await mountView()

    const accountCards = wrapper.findAll('.bg-surface-0.rounded-xl.shadow.p-4')
    expect(accountCards).toHaveLength(2)
  })

  it('shows no data message when balance has empty accounts', async () => {
    mockWalletStore.balance = { accounts: [] }
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('No data available')
  })

  it('shows empty state links to import and settings', async () => {
    mockActiveWalletStore.activeWalletId = null
    mockActiveWalletStore.activeWallet = null
    const wrapper = await mountView()

    const links = wrapper.findAll('a[href]')
    const hrefs = links.map((l) => l.attributes('href'))
    expect(hrefs).toContain('/import')
    expect(hrefs).toContain('/settings')
  })
})
