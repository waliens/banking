import { describe, it, expect } from 'vitest'
import { usePagination } from '../../src/composables/usePagination'

describe('usePagination', () => {
  it('initializes with defaults', () => {
    const { page, pageSize, start, totalPages, totalRecords } = usePagination()

    expect(page.value).toBe(0)
    expect(pageSize.value).toBe(50)
    expect(start.value).toBe(0)
    expect(totalRecords.value).toBe(0)
    expect(totalPages.value).toBe(0)
  })

  it('accepts custom page size', () => {
    const { pageSize } = usePagination(25)
    expect(pageSize.value).toBe(25)
  })

  it('computes start offset', () => {
    const { page, pageSize, start } = usePagination(10)
    page.value = 3
    expect(start.value).toBe(30)
  })

  it('computes total pages', () => {
    const { totalRecords, totalPages } = usePagination(10)

    totalRecords.value = 25
    expect(totalPages.value).toBe(3) // ceil(25/10)

    totalRecords.value = 30
    expect(totalPages.value).toBe(3)

    totalRecords.value = 0
    expect(totalPages.value).toBe(0)
  })

  it('handles onPage event from PrimeVue Paginator', () => {
    const { page, pageSize, onPage } = usePagination()

    onPage({ page: 2, rows: 25 })

    expect(page.value).toBe(2)
    expect(pageSize.value).toBe(25)
  })

  it('resets page to 0', () => {
    const { page, reset } = usePagination()
    page.value = 5

    reset()

    expect(page.value).toBe(0)
  })
})
