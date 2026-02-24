import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import IconPicker from '../../../src/components/common/IconPicker.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } })

const stubComponents = {
  Button: {
    template: '<button @click="$emit(\'click\', $event)"><slot />{{ label }}</button>',
    props: ['label', 'outlined', 'size', 'text', 'severity'],
  },
  InputText: {
    template: '<input />',
    props: ['modelValue', 'placeholder', 'size'],
  },
  Popover: {
    template: '<div class="popover-stub"><slot /></div>',
    methods: { toggle() {}, hide() {} },
  },
}

describe('IconPicker', () => {
  function mountComponent(props = {}) {
    return mount(IconPicker, {
      props: { modelValue: null, ...props },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
  }

  it('renders without error', () => {
    const wrapper = mountComponent()
    expect(wrapper.exists()).toBe(true)
  })

  it('has a trigger button', () => {
    const wrapper = mountComponent()
    const btn = wrapper.find('button')
    expect(btn.exists()).toBe(true)
  })

  it('shows icon class when modelValue is set', () => {
    const wrapper = mountComponent({ modelValue: 'fas fa-home' })
    const icon = wrapper.find('i.fas')
    expect(icon.exists()).toBe(true)
  })

  it('shows placeholder text when no icon selected', () => {
    const wrapper = mountComponent({ modelValue: null })
    // Should show the translation key for the placeholder
    expect(wrapper.text()).toContain('categories.icon')
  })

  it('displays modelValue label when set', () => {
    const wrapper = mountComponent({ modelValue: 'fas fa-home' })
    expect(wrapper.text()).toContain('fas fa-home')
  })
})
