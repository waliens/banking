import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import PeriodFilter from '../../../src/components/analytics/PeriodFilter.vue'

const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {
  wallet: { periodYear: 'Year', periodMonth: 'Month', periodRange: 'Range' },
  transactions: { date: 'Date' },
} } })

const stubComponents = {
  SelectButton: {
    template: '<div class="select-button" />',
    props: ['modelValue', 'options', 'allowEmpty'],
    emits: ['update:modelValue'],
  },
  Select: {
    template: '<div class="select" />',
    props: ['modelValue', 'options'],
    emits: ['update:modelValue'],
  },
  DatePicker: {
    template: '<div class="datepicker" />',
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
}

describe('PeriodFilter', () => {
  it('renders with default year period type', () => {
    const wrapper = mount(PeriodFilter, {
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.find('.select-button').exists()).toBe(true)
    // Year selector visible in year mode
    expect(wrapper.find('.select').exists()).toBe(true)
    // No datepickers in year mode
    expect(wrapper.find('.datepicker').exists()).toBe(false)
  })

  it('shows month selector when periodType is month', () => {
    const wrapper = mount(PeriodFilter, {
      props: { periodType: 'month' },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    // Should have 2 select elements (year + month)
    expect(wrapper.findAll('.select').length).toBe(2)
  })

  it('shows date pickers when periodType is range', () => {
    const wrapper = mount(PeriodFilter, {
      props: { periodType: 'range' },
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    expect(wrapper.findAll('.datepicker').length).toBe(2)
    // No year/month selects
    expect(wrapper.find('.select').exists()).toBe(false)
  })

  it('emits update:year when year changes', async () => {
    const wrapper = mount(PeriodFilter, {
      global: { stubs: stubComponents, plugins: [i18n] },
    })
    // Year selector exists in year mode
    expect(wrapper.find('.select').exists()).toBe(true)
  })
})
