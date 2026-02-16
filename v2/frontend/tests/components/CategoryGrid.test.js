import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CategoryGrid from '../../src/components/tagger/CategoryGrid.vue'

const categories = [
  { id: 1, name: 'Food', color: '#ef4444' },
  { id: 2, name: 'Transport', color: '#3b82f6' },
  { id: 3, name: 'Housing', color: '#22c55e' },
]

const transaction = {
  id: 10,
  description: 'Grocery store',
  date: '2025-01-15',
  amount: 42.5,
  id_source: 1,
}

describe('CategoryGrid', () => {
  it('renders category boxes from props', () => {
    const wrapper = mount(CategoryGrid, {
      props: { categories, transaction },
    })

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(3)
    expect(buttons[0].text()).toBe('Food')
    expect(buttons[1].text()).toBe('Transport')
    expect(buttons[2].text()).toBe('Housing')
  })

  it('shows transaction context card when transaction prop is provided', () => {
    const wrapper = mount(CategoryGrid, {
      props: { categories, transaction },
    })

    expect(wrapper.text()).toContain('Grocery store')
    expect(wrapper.text()).toContain('2025-01-15')
    expect(wrapper.text()).toContain('42.5')
  })

  it('does not show transaction context card when no transaction', () => {
    const wrapper = mount(CategoryGrid, {
      props: { categories },
    })

    expect(wrapper.text()).not.toContain('Grocery store')
  })

  it('emits select with category id on box click', async () => {
    const wrapper = mount(CategoryGrid, {
      props: { categories, transaction },
    })

    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('select')).toHaveLength(1)
    expect(wrapper.emitted('select')[0]).toEqual([2])
  })

  it('applies category color as left border style', () => {
    const wrapper = mount(CategoryGrid, {
      props: { categories },
    })

    const firstButton = wrapper.findAll('button')[0]
    expect(firstButton.attributes('style')).toContain('border-left-color: #ef4444')
  })
})
