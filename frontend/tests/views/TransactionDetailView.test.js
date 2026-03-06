import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../../src/stores/categories', () => ({
  useCategoryStore: vi.fn(() => ({
    categories: [],
    fetchCategories: vi.fn().mockResolvedValue([]),
  })),
}))

vi.mock('../../src/stores/ml', () => ({
  useMLStore: vi.fn(() => ({
    predictions: {},
    predictTransactions: vi.fn().mockResolvedValue({}),
  })),
}))

let mockActiveWalletId = null
let mockWalletAccountIds = []

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => ({
    get activeWalletId() { return mockActiveWalletId },
    get walletAccountIds() { return mockWalletAccountIds },
  })),
}))

const mockRoute = { params: { id: '42' } }
const mockRouter = { back: vi.fn() }

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}))

import api from '../../src/services/api'
import TransactionDetailView from '../../src/views/TransactionDetailView.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

let mockFetchGroup = vi.fn().mockResolvedValue({})

vi.mock('../../src/stores/transactionGroups', () => ({
  useTransactionGroupStore: vi.fn(() => ({
    fetchGroup: (...args) => mockFetchGroup(...args),
    createGroup: vi.fn().mockResolvedValue({}),
    updateGroup: vi.fn().mockResolvedValue({}),
    deleteGroup: vi.fn().mockResolvedValue({}),
    setGroupCategorySplits: vi.fn().mockResolvedValue({}),
    clearGroupCategorySplits: vi.fn().mockResolvedValue({}),
  })),
}))

const stubComponents = {
  Button: { template: '<button @click="$emit(\'click\')" :data-testid="$attrs[\'data-testid\']" :disabled="disabled"><slot />{{ label }}</button>', props: ['label', 'severity', 'size', 'icon', 'text', 'disabled'] },
  TransactionDetail: { template: '<div data-testid="transaction-detail" />', props: ['transaction'] },
  TransactionGroupDetail: { template: '<div data-testid="transaction-group-detail" />', props: ['group'] },
  TransactionGroupDialog: { template: '<div data-testid="transaction-group-dialog" v-if="visible" :data-wallet-id="walletId" :data-wallet-account-ids="JSON.stringify(walletAccountIds)" />', props: ['visible', 'group', 'initialTransaction', 'walletId', 'walletAccountIds'] },
  DuplicateCandidates: { template: '<div data-testid="duplicate-candidates" />', props: ['transactionId'] },
  CurrencyDisplay: { template: '<span />', props: ['amount', 'currencySymbol'] },
  AccountDisplay: { template: '<span />', props: ['account'] },
  CategorySelect: { template: '<div class="category-select-stub" />', props: ['modelValue', 'placeholder', 'showClear'] },
  InputNumber: { template: '<input />', props: ['modelValue', 'minFractionDigits', 'maxFractionDigits'] },
  SelectButton: { template: '<div />', props: ['modelValue', 'options'] },
  'router-link': { template: '<a :href="to"><slot /></a>', props: ['to'] },
}

function makeTx(overrides = {}) {
  return {
    id: 42,
    date: '2024-01-15',
    description: 'Test transaction',
    amount: -50.00,
    currency: { symbol: '$', short_name: 'USD' },
    source: { id: 1, name: 'Checking' },
    dest: null,
    category_splits: [],
    id_duplicate_of: null,
    id_transaction_group: null,
    is_reviewed: false,
    ...overrides,
  }
}

describe('TransactionDetailView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockFetchGroup = vi.fn().mockResolvedValue({})
    mockRoute.params.id = '42'
    mockActiveWalletId = 1
    mockWalletAccountIds = [10, 20]
  })

  it('fetches transaction on mount using route param', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/transactions/42')
  })

  it('shows loading spinner while fetching', () => {
    api.get.mockReturnValue(new Promise(() => {})) // never resolves

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })

    expect(wrapper.find('.pi-spinner').exists()).toBe(true)
  })

  it('renders TransactionDetail component after load', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="transaction-detail"]').exists()).toBe(true)
  })

  it('shows DuplicateCandidates section', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="duplicate-candidates"]').exists()).toBe(true)
  })

  it('shows duplicate-of card when id_duplicate_of is set', async () => {
    const tx = makeTx({ id_duplicate_of: 99 })
    const originalTx = makeTx({ id: 99, description: 'Original' })

    api.get
      .mockResolvedValueOnce({ data: tx })        // fetch transaction
      .mockResolvedValueOnce({ data: originalTx }) // fetch original

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    // Should have a link to the original transaction
    const links = wrapper.findAll('a')
    const originalLink = links.find((l) => l.attributes('href') === '/transactions/99')
    expect(originalLink).toBeTruthy()
  })

  it('hides duplicate-of card when not a duplicate', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    // No link to /transactions/undefined or other duplicate-related content
    const links = wrapper.findAll('a')
    const duplicateLink = links.find((l) => l.attributes('href')?.includes('/transactions/null'))
    expect(duplicateLink).toBeFalsy()
  })

  it('shows TransactionGroupDetail when id_transaction_group is set', async () => {
    const tx = makeTx({ id_transaction_group: 5 })
    const groupData = { id: 5, name: 'Trip', transactions: [] }

    api.get.mockResolvedValueOnce({ data: tx })
    mockFetchGroup.mockResolvedValueOnce(groupData)

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="transaction-group-detail"]').exists()).toBe(true)
    expect(mockFetchGroup).toHaveBeenCalledWith(5, 1)
  })

  it('hides group section when no group', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="transaction-group-detail"]').exists()).toBe(false)
  })

  it('back button calls router.back()', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    const backButton = wrapper.findAll('button').find((b) => b.text().includes(''))
    await wrapper.findAll('button')[0].trigger('click')

    expect(mockRouter.back).toHaveBeenCalled()
  })

  it('shows "Link transactions" button when no group', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="link-transactions-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="edit-group-btn"]').exists()).toBe(false)
  })

  it('shows "Edit group" button when group exists', async () => {
    const tx = makeTx({ id_transaction_group: 5 })
    const groupData = { id: 5, name: 'Trip', transactions: [{ id: 42, amount: '50.00', id_source: 1 }] }

    api.get.mockResolvedValueOnce({ data: tx })
    mockFetchGroup.mockResolvedValueOnce(groupData)

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="edit-group-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="remove-from-group-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="link-transactions-btn"]').exists()).toBe(false)
  })

  it('opens TransactionGroupDialog on link button click', async () => {
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="transaction-group-dialog"]').exists()).toBe(false)

    await wrapper.find('[data-testid="link-transactions-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="transaction-group-dialog"]').exists()).toBe(true)
  })

  it('disables "Link transactions" button when no wallet is active', async () => {
    mockActiveWalletId = null
    mockWalletAccountIds = []
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    const linkBtn = wrapper.find('[data-testid="link-transactions-btn"]')
    expect(linkBtn.exists()).toBe(true)
    expect(linkBtn.attributes('disabled')).toBeDefined()
  })

  it('passes wallet context to TransactionGroupDialog', async () => {
    mockActiveWalletId = 7
    mockWalletAccountIds = [10, 20, 30]
    api.get.mockResolvedValueOnce({ data: makeTx() })

    const wrapper = mount(TransactionDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await flushPromises()

    // Open the dialog
    await wrapper.find('[data-testid="link-transactions-btn"]').trigger('click')
    await flushPromises()

    const dialog = wrapper.find('[data-testid="transaction-group-dialog"]')
    expect(dialog.exists()).toBe(true)
    expect(dialog.attributes('data-wallet-id')).toBe('7')
    expect(dialog.attributes('data-wallet-account-ids')).toBe('[10,20,30]')
  })
})
