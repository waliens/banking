import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MLSuggestion from '../../src/components/MLSuggestion.vue'

describe('MLSuggestion', () => {
  it('renders category name and probability', () => {
    const wrapper = mount(MLSuggestion, {
      props: {
        categoryName: 'Food',
        categoryColor: '#FF0000',
        probability: 0.85,
      },
    })

    expect(wrapper.text()).toContain('Food')
    expect(wrapper.text()).toContain('85%')
  })

  it('does not render when categoryName is null', () => {
    const wrapper = mount(MLSuggestion, {
      props: {
        categoryName: null,
        categoryColor: null,
        probability: 0,
      },
    })

    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('emits accept on click', async () => {
    const wrapper = mount(MLSuggestion, {
      props: {
        categoryName: 'Transport',
        categoryColor: '#0000FF',
        probability: 0.92,
      },
    })

    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('accept')).toHaveLength(1)
  })

  it('applies category color as style', () => {
    const wrapper = mount(MLSuggestion, {
      props: {
        categoryName: 'Food',
        categoryColor: '#FF0000',
        probability: 0.7,
      },
    })

    const btn = wrapper.find('button')
    expect(btn.attributes('style')).toContain('#FF0000')
  })
})
