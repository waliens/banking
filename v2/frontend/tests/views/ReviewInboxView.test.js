import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
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

const stubComponents = {
  DataTable: { template: '<div><slot /></div>', props: ['value', 'loading', 'lazy', 'paginator', 'rows', 'totalRecords', 'dataKey', 'stripedRows', 'responsiveLayout'] },
  Column: { template: '<div />', props: ['field', 'header', 'style'] },
  Select: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'] },
  Button: { template: '<button @click="$emit(\'click\')">{{ label }}</button>', props: ['label', 'severity', 'size', 'icon', 'disabled', 'text', 'outlined'] },
  MLSuggestion: { template: '<div />', props: ['categoryName', 'categoryColor', 'probability'] },
  CurrencyDisplay: { template: '<span />', props: ['amount', 'currencySymbol', 'showSign', 'colored'] },
  InputText: { template: '<input />', props: ['modelValue', 'placeholder'] },
  InputNumber: { template: '<input />', props: ['modelValue', 'placeholder', 'minFractionDigits'] },
  DatePicker: { template: '<input />', props: ['modelValue', 'dateFormat', 'placeholder', 'showIcon'] },
  ToggleSwitch: { template: '<input type="checkbox" />', props: ['modelValue'] },
  Drawer: { template: '<div><slot /></div>', props: ['visible', 'position', 'header'] },
  TransactionDetail: { template: '<div />', props: ['transaction', 'showFullDetails'] },
  AccountDisplay: { template: '<span />', props: ['account'] },
  AccountSelect: { template: '<select />', props: ['modelValue', 'placeholder', 'showClear'] },
  CategorySelect: { template: '<select />', props: ['modelValue', 'placeholder', 'showClear'] },
  'router-link': { template: '<a><slot /></a>', props: ['to'] },
}

describe('ReviewInboxView', () => {
  let transactionStore

  beforeEach(() => {
    setActivePinia(createPinia())
    transactionStore = useTransactionStore()
    vi.clearAllMocks()

    // Default mock responses for onMounted calls
    api.get
      .mockResolvedValueOnce({ data: [] })           // /transactions
      .mockResolvedValueOnce({ data: { count: 0 } }) // /transactions/count
      .mockResolvedValueOnce({ data: { count: 0 } }) // /transactions/review-inbox/count
  })

  it('fetches transactions with wallet scoping params on mount', async () => {
    mount(ReviewInboxView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

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
    mount(ReviewInboxView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

    expect(api.get).toHaveBeenCalledWith('/transactions/review-inbox/count')
  })
})
