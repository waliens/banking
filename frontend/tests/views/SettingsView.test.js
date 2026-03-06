import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import ToastService from 'primevue/toastservice'
import PrimeVue from 'primevue/config'
import { useAuthStore } from '../../src/stores/auth'

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({})),
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({ params: {} })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

vi.mock('../../src/stores/activeWallet', () => ({
  useActiveWalletStore: vi.fn(() => ({
    activeWalletId: 1,
    setActiveWallet: vi.fn(),
  })),
}))

import SettingsView from '../../src/views/SettingsView.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  settings: {
    title: 'Settings',
    accounts: 'Accounts',
    categories: 'Categories',
    mlModels: 'ML Models',
    rules: 'Tag Rules',
    wallets: 'Wallets',
    defaultWallet: 'Default wallet',
    changePassword: 'Change Password',
    newPassword: 'New Password',
    confirmPassword: 'Confirm Password',
    passwordChanged: 'Password changed',
    passwordMismatch: 'Passwords do not match',
    trainNow: 'Train Now',
    noModels: 'No models',
    filename: 'Filename',
    status: 'Status',
    score: 'Score',
    samples: 'Samples',
    active: 'Active',
    trainStarted: 'Training started',
    trainFailed: 'Training failed',
    mergeAccounts: 'Merge Accounts',
    mergeRepresentative: 'Keep',
    mergeAlias: 'Remove',
    mergeWarning: 'Cannot be undone',
    mergeButton: 'Merge',
  },
  common: { save: 'Save', cancel: 'Cancel', create: 'Create', edit: 'Edit' },
  accounts: { title: 'Accounts', initialBalance: 'Initial Balance' },
  categories: { title: 'Categories', name: 'Name', color: 'Color', parent: 'Parent' },
  rules: { title: 'Rules', name: 'Name', pattern: 'Pattern', amountRange: 'Range', amountMin: 'Min', amountMax: 'Max', priority: 'Priority', active: 'Active', apply: 'Apply', applied: 'Applied' },
  transactions: { title: 'Transactions', category: 'Category', date: 'Date' },
  ml: { train: 'Train' },
  nav: { wallets: 'Wallets' },
} } })

const stubComponents = {
  Card: { template: '<div><slot name="title" /><slot name="content" /></div>' },
  Button: { template: '<button @click="$emit(\'click\')"><slot /></button>', props: ['icon', 'label', 'loading', 'text', 'rounded', 'severity', 'size', 'title', 'disabled'] },
  Password: { template: '<input type="password" />', props: ['modelValue', 'feedback', 'toggleMask', 'inputClass'] },
  Tabs: { template: '<div><slot /></div>', props: ['value'] },
  TabList: { template: '<div><slot /></div>' },
  Tab: { template: '<div><slot /></div>', props: ['value'] },
  TabPanels: { template: '<div><slot /></div>' },
  TabPanel: { template: '<div><slot /></div>', props: ['value'] },
  DataTable: { template: '<div><slot /></div>', props: ['value', 'loading', 'lazy', 'paginator', 'rows', 'totalRecords', 'first', 'rowsPerPageOptions', 'stripedRows', 'responsiveLayout'] },
  Column: { template: '<div />', props: ['field', 'header', 'style'] },
  Tag: { template: '<span>{{ value }}</span>', props: ['value', 'severity'] },
  ToggleSwitch: { template: '<input type="checkbox" />', props: ['modelValue'] },
  Tree: { template: '<div />', props: ['value'] },
  Dialog: { template: '<div><slot /><slot name="footer" /></div>', props: ['visible', 'header', 'modal'] },
  InputText: { template: '<input />', props: ['modelValue'] },
  InputNumber: { template: '<input />', props: ['modelValue', 'mode', 'minFractionDigits'] },
  ColorPicker: { template: '<input />', props: ['modelValue'] },
  Select: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'showClear', 'placeholder'] },
  MultiSelect: { template: '<select />', props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'] },
}

describe('SettingsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders the settings title', () => {
    const wrapper = mount(SettingsView, { global: { stubs: stubComponents, plugins: [i18n, PrimeVue, ToastService] } })
    expect(wrapper.text()).toContain('Settings')
  })

  it('renders all five tab labels including Wallets', () => {
    const wrapper = mount(SettingsView, { global: { stubs: stubComponents, plugins: [i18n, PrimeVue, ToastService] } })
    expect(wrapper.text()).toContain('Wallets')
    expect(wrapper.text()).toContain('Accounts')
    expect(wrapper.text()).toContain('Categories')
    expect(wrapper.text()).toContain('Tag Rules')
    expect(wrapper.text()).toContain('ML Models')
  })

  it('renders the password change form', () => {
    const wrapper = mount(SettingsView, { global: { stubs: stubComponents, plugins: [i18n, PrimeVue, ToastService] } })
    expect(wrapper.text()).toContain('Change Password')
    expect(wrapper.text()).toContain('New Password')
    expect(wrapper.text()).toContain('Confirm Password')
  })
})
