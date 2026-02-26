import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import CreateTagRuleDialog from '../../../src/components/transactions/CreateTagRuleDialog.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const stubs = {
  Dialog: { template: '<div><slot /><slot name="footer" /></div>', props: ['visible', 'header', 'modal'] },
  Button: { template: '<button :disabled="disabled">{{ label }}</button>', props: ['label', 'icon', 'disabled', 'loading', 'severity', 'text'] },
  Checkbox: { template: '<input type="checkbox" />', props: ['modelValue', 'binary', 'inputId'] },
  InputText: { template: '<input />', props: ['modelValue', 'disabled', 'invalid'] },
  InputNumber: { template: '<input type="number" />', props: ['modelValue', 'disabled', 'mode', 'minFractionDigits'] },
  CategorySelect: { template: '<select />', props: ['modelValue', 'placeholder', 'showClear'] },
  AccountSelect: { template: '<select />', props: ['modelValue', 'showClear', 'disabled'] },
}

describe('CreateTagRuleDialog', () => {
  function mountComponent(props = {}) {
    const pinia = createPinia()
    setActivePinia(pinia)
    return mount(CreateTagRuleDialog, {
      props: {
        visible: true,
        transaction: {
          description: 'Test transaction',
          amount: -25.0,
          id_source: 1,
          id_dest: null,
          id_category: null,
        },
        ...props,
      },
      global: {
        stubs,
        plugins: [i18n, pinia],
      },
    })
  }

  it('renders without error', () => {
    const wrapper = mountComponent()
    expect(wrapper.exists()).toBe(true)
  })

  it('does not mark valid regex as invalid', () => {
    const wrapper = mountComponent()
    expect(wrapper.vm.isRegexValid).toBe(true)
  })

  it('marks invalid regex pattern as invalid', async () => {
    const wrapper = mountComponent()
    wrapper.vm.matchDescription = '[invalid'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.isRegexValid).toBe(false)
  })

  it('disables save button when regex is invalid', async () => {
    const wrapper = mountComponent()
    wrapper.vm.matchDescription = '[invalid'
    wrapper.vm.categoryId = 1
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.canSave).toBe(false)
  })

  it('allows save when regex is valid', async () => {
    const wrapper = mountComponent()
    wrapper.vm.matchDescription = '^colruyt.*store$'
    wrapper.vm.categoryId = 1
    wrapper.vm.includeDescription = true
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.isRegexValid).toBe(true)
    expect(wrapper.vm.canSave).toBe(true)
  })
})
