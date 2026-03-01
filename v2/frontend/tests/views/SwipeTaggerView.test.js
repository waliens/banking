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
        remaining: 'remaining',
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

  it('shows allDone state when API returns empty transaction list', async () => {
    setupApiMock([], [{ id: 10, name: 'Food', id_parent: null }])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    expect(wrapper.find('.pi-check-circle').exists()).toBe(true)
    expect(wrapper.text()).toContain('All caught up!')
    // Hint bar should NOT be visible in allDone state
    expect(wrapper.text()).not.toContain('← Categorize')
  })

  it('counter shows processedCount and reviewCount', async () => {
    setupApiMock(sampleTxs, [])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // processedCount starts at 0, reviewCount comes from review-inbox/count API
    expect(wrapper.text()).toContain('0 done')
    expect(wrapper.text()).toContain('remaining')
  })

  it('selecting a parent category with children transitions to pick-child mode', async () => {
    const categories = [
      { id: 10, name: 'Food', id_parent: null },
      { id: 11, name: 'Groceries', id_parent: 10 },
      { id: 12, name: 'Restaurants', id_parent: 10 },
    ]
    setupApiMock(sampleTxs, categories)
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Simulate swipe left to enter pick-parent mode
    wrapper.vm.mode = 'pick-parent'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Pick a category')

    // Directly call selectParent since stub doesn't propagate custom events
    await wrapper.vm.selectParent(10)
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.mode).toBe('pick-child')
    expect(wrapper.text()).toContain('Pick a sub-category')
  })

  it('selecting a leaf parent category (no children) applies category directly', async () => {
    const categories = [
      { id: 10, name: 'Food', id_parent: null },
      // No children for Food — it's a leaf
    ]
    setupApiMock(sampleTxs, categories)
    api.put.mockResolvedValue({ data: { ...sampleTxs[0], category: { id: 10, name: 'Food' } } })
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Enter pick-parent mode
    wrapper.vm.mode = 'pick-parent'
    await wrapper.vm.$nextTick()

    // Directly call selectParent for a leaf category
    await wrapper.vm.selectParent(10)
    await new Promise((r) => setTimeout(r, 50))

    // Should have called setCategory API
    expect(api.put).toHaveBeenCalledWith('/transactions/1/category/10')
  })

  it('back button in pick-parent mode returns to card mode', async () => {
    setupApiMock(sampleTxs, [{ id: 10, name: 'Food', id_parent: null }])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Enter pick-parent mode
    wrapper.vm.mode = 'pick-parent'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Pick a category')

    // Click back button
    const backBtn = wrapper.find('button.text-primary-500')
    await backBtn.trigger('click')

    expect(wrapper.vm.mode).toBe('card')
  })

  it('back button in pick-child mode returns to pick-parent mode', async () => {
    const categories = [
      { id: 10, name: 'Food', id_parent: null },
      { id: 11, name: 'Groceries', id_parent: 10 },
    ]
    setupApiMock(sampleTxs, categories)
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Enter pick-child mode
    wrapper.vm.mode = 'pick-child'
    wrapper.vm.selectedParent = 10
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Pick a sub-category')

    // Click back button
    const backBtn = wrapper.find('button.text-primary-500')
    await backBtn.trigger('click')

    expect(wrapper.vm.mode).toBe('pick-parent')
    expect(wrapper.vm.selectedParent).toBeNull()
  })

  it('detail mode shows TransactionDetail component', async () => {
    setupApiMock(sampleTxs, [])
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Enter detail mode (swipe down)
    wrapper.vm.mode = 'detail'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Detail')
    const detail = wrapper.find('.transaction-detail')
    expect(detail.exists()).toBe(true)
  })

  it('ML prediction is displayed when available', async () => {
    const predictions = [
      { transaction_id: 1, category_id: 10, category_name: 'Food', category_color: '#ff0000', probability: 0.95 },
    ]
    setupApiMock(sampleTxs, [])
    api.post.mockImplementation(() => Promise.resolve({ data: { predictions } }))
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // When prediction is available, the MLSuggestion stub renders and swipe hint is shown
    expect(wrapper.text()).toContain('Swipe right to accept')
  })

  it('swipe right with no prediction does nothing (handler guards)', async () => {
    setupApiMock(sampleTxs, [])
    // No predictions returned
    api.post.mockImplementation(() => Promise.resolve({ data: { predictions: [] } }))
    const wrapper = mountTagger()
    await new Promise((r) => setTimeout(r, 50))

    // Directly call handleSwipeRight — it should guard on missing prediction
    await wrapper.vm.handleSwipeRight()

    // setCategory should NOT have been called
    expect(api.put).not.toHaveBeenCalled()
    // Should still be on first card
    expect(wrapper.vm.currentIndex).toBe(0)
    expect(wrapper.vm.processedCount).toBe(0)
  })
})
