import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import CategorySelect from '../../../src/components/common/CategorySelect.vue'
import { useCategoryStore } from '../../../src/stores/categories'

vi.mock('../../../src/services/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      wallet: {
        categoriesSelected: '{n} selected',
        selectAll: 'Select all',
        deselectAll: 'Deselect all',
      },
    },
  },
})

const stubComponents = {
  InputText: {
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" :placeholder="placeholder" />',
    props: ['modelValue', 'placeholder'],
    emits: ['update:modelValue'],
  },
}

// Mock category data: two parent groups with children
const mockCategories = [
  { id: 1, name: 'Food', id_parent: null, icon: 'fas fa-utensils', color: '#e74c3c' },
  { id: 2, name: 'Groceries', id_parent: 1, icon: 'fas fa-cart-shopping', color: '#e67e22' },
  { id: 3, name: 'Restaurant', id_parent: 1, icon: 'fas fa-burger', color: '#f39c12' },
  { id: 10, name: 'Transport', id_parent: null, icon: 'fas fa-car', color: '#3498db' },
  { id: 11, name: 'Fuel', id_parent: 10, icon: 'fas fa-gas-pump', color: '#2ecc71' },
  { id: 12, name: 'Public Transit', id_parent: 10, icon: 'fas fa-bus', color: '#9b59b6' },
]

function populateStore() {
  const store = useCategoryStore()
  store.categories = mockCategories
  return store
}

describe('CategorySelect', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function mountComponent(props = {}, attachToDoc = false) {
    const opts = {
      props: { modelValue: null, ...props },
      global: {
        stubs: stubComponents,
        plugins: [i18n],
      },
    }
    if (attachToDoc) {
      opts.attachTo = document.body
    }
    return mount(CategorySelect, opts)
  }

  it('renders with placeholder when no value selected', () => {
    populateStore()
    const w = mountComponent({ placeholder: 'Pick a category' })
    expect(w.text()).toContain('Pick a category')
  })

  it('uses default placeholder when none provided', () => {
    populateStore()
    const w = mountComponent()
    expect(w.text()).toContain('Select category')
  })

  it('shows selected category name when modelValue is set', () => {
    populateStore()
    const w = mountComponent({ modelValue: 2 })
    expect(w.text()).toContain('Groceries')
  })

  it('shows selected category icon when modelValue is set', () => {
    populateStore()
    const w = mountComponent({ modelValue: 2 })
    const icon = w.find('i.fas.fa-cart-shopping')
    expect(icon.exists()).toBe(true)
  })

  it('opens dropdown on click', async () => {
    populateStore()
    const w = mountComponent({}, true)

    // Dropdown should not be visible initially
    expect(document.querySelector('[class*="fixed"]')).toBeNull()

    // Click the trigger button
    await w.find('button').trigger('click')

    // Dropdown should now be teleported to body
    const dropdown = document.querySelector('.fixed')
    expect(dropdown).not.toBeNull()
    expect(dropdown.textContent).toContain('Groceries')
    expect(dropdown.textContent).toContain('Restaurant')
    expect(dropdown.textContent).toContain('Fuel')

    w.unmount()
  })

  it('filters categories by search query', async () => {
    populateStore()
    const w = mountComponent({}, true)

    // Open dropdown
    await w.find('button').trigger('click')

    // Type search query into the input
    const input = document.querySelector('.fixed input')
    expect(input).not.toBeNull()

    // Simulate typing in search
    input.value = 'gro'
    input.dispatchEvent(new Event('input'))
    await w.vm.$nextTick()

    const dropdown = document.querySelector('.fixed')
    // Should show Groceries but not Restaurant, Fuel, Public Transit
    expect(dropdown.textContent).toContain('Groceries')
    expect(dropdown.textContent).not.toContain('Restaurant')
    expect(dropdown.textContent).not.toContain('Fuel')
    expect(dropdown.textContent).not.toContain('Public Transit')

    w.unmount()
  })

  it('shows no categories found when search matches nothing', async () => {
    populateStore()
    const w = mountComponent({}, true)

    await w.find('button').trigger('click')

    const input = document.querySelector('.fixed input')
    input.value = 'zzzznotfound'
    input.dispatchEvent(new Event('input'))
    await w.vm.$nextTick()

    const dropdown = document.querySelector('.fixed')
    expect(dropdown.textContent).toContain('No categories found')

    w.unmount()
  })

  it('emits update:modelValue when a category is selected', async () => {
    populateStore()
    const w = mountComponent({}, true)

    // Open dropdown
    await w.find('button').trigger('click')

    // Find and click a child category (Groceries)
    const items = document.querySelectorAll('.fixed .cursor-pointer')
    const groceriesItem = Array.from(items).find((el) => el.textContent.includes('Groceries'))
    expect(groceriesItem).not.toBeUndefined()

    groceriesItem.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0]).toEqual([2])

    w.unmount()
  })

  it('closes dropdown after single-select selection', async () => {
    populateStore()
    const w = mountComponent({}, true)

    await w.find('button').trigger('click')
    expect(document.querySelector('.fixed')).not.toBeNull()

    const items = document.querySelectorAll('.fixed .cursor-pointer')
    const groceriesItem = Array.from(items).find((el) => el.textContent.includes('Groceries'))
    groceriesItem.click()
    await w.vm.$nextTick()

    // Dropdown should be closed
    expect(document.querySelector('.fixed')).toBeNull()

    w.unmount()
  })

  it('shows clear button when showClear is true and value is set', () => {
    populateStore()
    const w = mountComponent({ modelValue: 2, showClear: true })
    // The clear button has pi-times icon
    const clearBtn = w.find('i.pi-times')
    expect(clearBtn.exists()).toBe(true)
  })

  it('does not show clear button when showClear is false', () => {
    populateStore()
    const w = mountComponent({ modelValue: 2, showClear: false })
    const clearBtn = w.find('i.pi-times')
    expect(clearBtn.exists()).toBe(false)
  })

  it('does not show clear button when showClear is true but no value', () => {
    populateStore()
    const w = mountComponent({ modelValue: null, showClear: true })
    const clearBtn = w.find('i.pi-times')
    expect(clearBtn.exists()).toBe(false)
  })

  it('clears value when clear button clicked (single)', async () => {
    populateStore()
    const w = mountComponent({ modelValue: 2, showClear: true })

    // Find the clear button (button containing pi-times)
    const clearIcon = w.find('i.pi-times')
    await clearIcon.element.parentElement.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0]).toEqual([null])
  })

  // Multi-select tests
  it('multi-select: shows placeholder when nothing selected', () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [], placeholder: 'Choose categories' })
    expect(w.text()).toContain('Choose categories')
  })

  it('multi-select: shows category names when 1-2 selected', () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2, 3] })
    expect(w.text()).toContain('Groceries')
    expect(w.text()).toContain('Restaurant')
  })

  it('multi-select: shows count when >2 selected', () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2, 3, 11] })
    expect(w.text()).toContain('3 selected')
  })

  it('multi-select: toggles category on click', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2] }, true)

    await w.find('button').trigger('click')

    // Click on Restaurant (id=3) to add it
    const items = document.querySelectorAll('.fixed .cursor-pointer')
    const restaurantItem = Array.from(items).find((el) => el.textContent.includes('Restaurant'))
    restaurantItem.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    // Should have both 2 and 3
    expect(w.emitted('update:modelValue')[0][0]).toEqual([2, 3])

    w.unmount()
  })

  it('multi-select: removes category when already selected', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2, 3] }, true)

    await w.find('button').trigger('click')

    // Click on Groceries (id=2) to remove it
    const items = document.querySelectorAll('.fixed .cursor-pointer')
    const groceriesItem = Array.from(items).find((el) => el.textContent.includes('Groceries'))
    groceriesItem.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0][0]).toEqual([3])

    w.unmount()
  })

  it('multi-select: dropdown stays open after selection', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [] }, true)

    await w.find('button').trigger('click')
    expect(document.querySelector('.fixed')).not.toBeNull()

    const items = document.querySelectorAll('.fixed .cursor-pointer')
    items[0].click()
    await w.vm.$nextTick()

    // Dropdown should still be open
    expect(document.querySelector('.fixed')).not.toBeNull()

    w.unmount()
  })

  it('multi-select: select all emits all child ids', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [] }, true)

    await w.find('button').trigger('click')

    // Find the "Select all" button
    const buttons = document.querySelectorAll('.fixed button')
    const selectAllBtn = Array.from(buttons).find((b) => b.textContent.includes('Select all'))
    expect(selectAllBtn).not.toBeUndefined()

    selectAllBtn.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    const emitted = w.emitted('update:modelValue')[0][0]
    // Should contain all 4 child ids
    expect(emitted).toEqual(expect.arrayContaining([2, 3, 11, 12]))
    expect(emitted).toHaveLength(4)

    w.unmount()
  })

  it('multi-select: deselect all emits empty array', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2, 3] }, true)

    await w.find('button').trigger('click')

    const buttons = document.querySelectorAll('.fixed button')
    const deselectAllBtn = Array.from(buttons).find((b) => b.textContent.includes('Deselect all'))
    expect(deselectAllBtn).not.toBeUndefined()

    deselectAllBtn.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0][0]).toEqual([])

    w.unmount()
  })

  it('multi-select: clear button emits empty array', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2, 3], showClear: true })

    const clearIcon = w.find('i.pi-times')
    expect(clearIcon.exists()).toBe(true)

    await clearIcon.element.parentElement.click()
    await w.vm.$nextTick()

    expect(w.emitted('update:modelValue')).toBeTruthy()
    expect(w.emitted('update:modelValue')[0][0]).toEqual([])
  })

  it('closes dropdown on click outside', async () => {
    populateStore()
    const w = mountComponent({}, true)

    // Open dropdown
    await w.find('button').trigger('click')
    expect(document.querySelector('.fixed')).not.toBeNull()

    // Click outside (on the body, outside the component)
    const outside = document.createElement('div')
    document.body.appendChild(outside)
    outside.click()

    // The click handler listens on document, so dispatch a real click
    document.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await w.vm.$nextTick()

    expect(document.querySelector('.fixed')).toBeNull()

    document.body.removeChild(outside)
    w.unmount()
  })

  it('toggles dropdown closed when clicking trigger while open', async () => {
    populateStore()
    const w = mountComponent({}, true)

    // Open
    await w.find('button').trigger('click')
    expect(document.querySelector('.fixed')).not.toBeNull()

    // Click trigger again to close
    await w.find('button').trigger('click')
    await w.vm.$nextTick()

    expect(document.querySelector('.fixed')).toBeNull()

    w.unmount()
  })

  it('shows select all / deselect all only in multi mode', async () => {
    populateStore()

    // Single mode
    const single = mountComponent({}, true)
    await single.find('button').trigger('click')
    let dropdown = document.querySelector('.fixed')
    expect(dropdown.textContent).not.toContain('Select all')
    single.unmount()

    // Multi mode
    const multi = mountComponent({ multiple: true, modelValue: [] }, true)
    await multi.find('button').trigger('click')
    dropdown = document.querySelector('.fixed')
    expect(dropdown.textContent).toContain('Select all')
    expect(dropdown.textContent).toContain('Deselect all')
    multi.unmount()
  })

  it('shows checkboxes in multi mode', async () => {
    populateStore()
    const w = mountComponent({ multiple: true, modelValue: [2] }, true)

    await w.find('button').trigger('click')
    const dropdown = document.querySelector('.fixed')

    // Selected item should have check-square icon
    const checkSquares = dropdown.querySelectorAll('i.pi-check-square')
    expect(checkSquares.length).toBeGreaterThanOrEqual(1)

    // Unselected items should have stop icon
    const stops = dropdown.querySelectorAll('i.pi-stop')
    expect(stops.length).toBeGreaterThanOrEqual(1)

    w.unmount()
  })

  it('displays group headers as non-selectable separators', async () => {
    populateStore()
    const w = mountComponent({}, true)

    await w.find('button').trigger('click')
    const dropdown = document.querySelector('.fixed')

    // Group headers should show parent names
    expect(dropdown.textContent).toContain('Food')
    expect(dropdown.textContent).toContain('Transport')

    w.unmount()
  })
})
