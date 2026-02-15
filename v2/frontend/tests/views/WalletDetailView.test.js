import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useWalletStore } from '../../src/stores/wallets'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({ params: { id: '1' } })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

import api from '../../src/services/api'
import WalletDetailView from '../../src/views/WalletDetailView.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Button: { template: '<button @click="$emit(\'click\')"><slot /></button>', props: ['icon', 'label', 'text', 'rounded', 'severity', 'size', 'outlined'] },
  Select: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue'] },
  DatePicker: { template: '<input />', props: ['modelValue', 'dateFormat', 'placeholder', 'showIcon'] },
  Tabs: { template: '<div><slot /></div>', props: ['value'] },
  TabList: { template: '<div><slot /></div>' },
  Tab: { template: '<div><slot /></div>', props: ['value'] },
  TabPanels: { template: '<div><slot /></div>' },
  TabPanel: { template: '<div><slot /></div>', props: ['value'] },
  IncomeExpenseChart: { template: '<div />', props: ['data'] },
  CategoryChart: { template: '<div />', props: ['data'] },
}

describe('WalletDetailView', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useWalletStore()
    vi.clearAllMocks()

    // Pre-populate wallets so the view can find the wallet
    store.wallets = [{ id: 1, name: 'Test Wallet', description: 'A test', accounts: [] }]

    // Mock all API calls triggered on mount
    api.get.mockImplementation((url) => {
      if (url.includes('/stats/balance')) return Promise.resolve({ data: { accounts: [] } })
      if (url.includes('/stats/income-expense')) return Promise.resolve({ data: { items: [] } })
      if (url.includes('/stats/per-category')) return Promise.resolve({ data: { items: [] } })
      if (url === '/wallets') return Promise.resolve({ data: store.wallets })
      return Promise.resolve({ data: {} })
    })
  })

  it('fetches stats data on mount', async () => {
    mount(WalletDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

    expect(api.get).toHaveBeenCalledWith('/wallets/1/stats/balance')
    expect(api.get).toHaveBeenCalledWith(
      '/wallets/1/stats/income-expense',
      expect.objectContaining({ params: expect.objectContaining({ year: expect.any(Number) }) })
    )
    expect(api.get).toHaveBeenCalledWith('/wallets/1/stats/per-category', expect.anything())
  })

  it('displays wallet name', async () => {
    const wrapper = mount(WalletDetailView, { global: { stubs: stubComponents, plugins: [i18n] } })
    await new Promise((r) => setTimeout(r, 10))

    expect(wrapper.text()).toContain('Test Wallet')
  })
})
