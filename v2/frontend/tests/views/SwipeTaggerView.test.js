import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => ({
    activeWalletId: 1,
    activeWallet: { id: 1, name: 'Test Wallet', accounts: [{ id_account: 10 }] },
    walletAccountIds: [10],
  })),
}))

import api from '../../src/services/api'
import SwipeTaggerView from '../../src/views/SwipeTaggerView.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      tagger: {
        title: 'Swipe Tagger',
        back: 'Back',
        processed: 'done',
        allDone: 'All caught up!',
        allDoneDesc: 'No more transactions to review.',
        backToReview: 'Back to Review',
        skip: 'Reviewed',
        accept: 'Accept',
        categorize: 'Categorize',
        swipeRightToAccept: 'Swipe right to accept',
        pickCategory: 'Pick a category',
        pickSubCategory: 'Pick a sub-category',
        hintLeft: 'Categorize',
        hintUp: 'Skip',
        hintRight: 'Accept',
        hintDown: 'Detail',
        detail: 'Detail',
      },
      transactions: {
        effectiveAmount: 'Effective amount',
      },
    },
  },
})

const stubComponents = {
  Button: { template: '<button @click="$emit(\'click\')">{{ label }}</button>', props: ['label', 'icon', 'severity', 'size'] },
  MLSuggestion: { template: '<span />', props: ['categoryName', 'categoryColor', 'probability'] },
  CategoryGrid: { template: '<div class="category-grid" />', props: ['categories', 'transaction'] },
  TransactionDetail: { template: '<div class="transaction-detail" />', props: ['transaction'] },
  CurrencyDisplay: { template: '<span>{{ amount }}</span>', props: ['amount', 'currencySymbol', 'showSign', 'colored'] },
}

const routerLinkStub = { template: '<a><slot /></a>', props: ['to'] }

function setupApiMock(txs = [], categories = []) {
  api.get.mockImplementation((url) => {
    if (url === '/transactions') return Promise.resolve({ data: txs })
    if (url === '/transactions/count') return Promise.resolve({ data: { count: txs.length } })
    if (url === '/transactions/review-inbox/count') return Promise.resolve({ data: { count: txs.length } })
    if (url === '/categories') return Promise.resolve({ data: categories })
    return Promise.resolve({ data: {} })
  })
  api.post.mockImplementation(() => Promise.resolve({ data: { predictions: [] } }))
}

function mountTagger() {
  return mount(SwipeTaggerView, {
    global: {
      stubs: { ...stubComponents, 'router-link': routerLinkStub },
      plugins: [i18n],
    },
  })
}

const sampleTxs = [
  { id: 1, description: 'Grocery', date: '2025-01-15', amount: 42.5, id_source: 1, source: { name: 'Main' }, currency: { symbol: '€' } },
  { id: 2, description: 'Salary', date: '2025-01-14', amount: 3000, id_source: null, source: { name: 'Main' }, currency: { symbol: '€' } },
]

describe('SwipeTaggerView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('shows "All caught up" when no transactions', async () => {
    setupApiMock([], [])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    expect(wrapper.text()).toContain('All caught up!')
    expect(wrapper.text()).toContain('No more transactions to review.')
  })

  it('renders card content when transactions exist', async () => {
    setupApiMock(sampleTxs, [])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    expect(wrapper.text()).toContain('42.5')
    expect(wrapper.text()).toContain('Grocery')
    expect(wrapper.text()).toContain('2025-01-15')
  })

  it('shows hint bar with 4 directions in card mode', async () => {
    setupApiMock(sampleTxs, [])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    expect(wrapper.text()).toContain('Categorize')
    expect(wrapper.text()).toContain('Skip')
    expect(wrapper.text()).toContain('Detail')
    expect(wrapper.text()).toContain('Accept')
  })

  it('passes wallet scoping params when loading batch', async () => {
    setupApiMock(sampleTxs, [])
    mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    expect(api.get).toHaveBeenCalledWith('/transactions', {
      params: expect.objectContaining({
        wallet: 1,
        wallet_external_only: true,
      }),
    })
  })
})
