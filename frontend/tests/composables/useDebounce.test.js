import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useDebounce } from '../../src/composables/useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initializes with the source value', () => {
    const source = ref('hello')
    const debounced = useDebounce(source)
    expect(debounced.value).toBe('hello')
  })

  it('does not update immediately on source change', async () => {
    const source = ref('a')
    const debounced = useDebounce(source, 300)

    source.value = 'b'
    await nextTick()

    expect(debounced.value).toBe('a') // not yet updated
  })

  it('updates after delay', async () => {
    const source = ref('a')
    const debounced = useDebounce(source, 200)

    source.value = 'b'
    await nextTick()

    vi.advanceTimersByTime(200)
    expect(debounced.value).toBe('b')
  })

  it('resets timer on rapid changes (only last value wins)', async () => {
    const source = ref('a')
    const debounced = useDebounce(source, 300)

    source.value = 'b'
    await nextTick()
    vi.advanceTimersByTime(100)

    source.value = 'c'
    await nextTick()
    vi.advanceTimersByTime(100)

    source.value = 'd'
    await nextTick()

    // only 200ms since last change, should still be 'a'
    expect(debounced.value).toBe('a')

    vi.advanceTimersByTime(300)
    expect(debounced.value).toBe('d')
  })

  it('uses default 300ms delay', async () => {
    const source = ref('x')
    const debounced = useDebounce(source)

    source.value = 'y'
    await nextTick()

    vi.advanceTimersByTime(299)
    expect(debounced.value).toBe('x')

    vi.advanceTimersByTime(1)
    expect(debounced.value).toBe('y')
  })
})
