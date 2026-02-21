import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock Vue lifecycle hooks before importing the composable
const unmountCallbacks = []
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: (cb) => unmountCallbacks.push(cb),
  }
})

import { useInfiniteScroll } from '../../src/composables/useInfiniteScroll'

describe('useInfiniteScroll', () => {
  let observeCallback
  let mockObserve
  let mockDisconnect

  beforeEach(() => {
    unmountCallbacks.length = 0
    mockObserve = vi.fn()
    mockDisconnect = vi.fn()

    global.IntersectionObserver = vi.fn((cb) => {
      observeCallback = cb
      return {
        observe: mockObserve,
        disconnect: mockDisconnect,
      }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('calls callback when sentinel intersects', async () => {
    const sentinel = ref(document.createElement('div'))
    const callback = vi.fn()

    useInfiniteScroll(sentinel, callback)

    // Simulate intersection
    observeCallback([{ isIntersecting: true }])

    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('does not call callback when not intersecting', () => {
    const sentinel = ref(document.createElement('div'))
    const callback = vi.fn()

    useInfiniteScroll(sentinel, callback)

    observeCallback([{ isIntersecting: false }])

    expect(callback).not.toHaveBeenCalled()
  })

  it('does not call when enabled is false', () => {
    const sentinel = ref(document.createElement('div'))
    const callback = vi.fn()
    const enabled = ref(false)

    useInfiniteScroll(sentinel, callback, { enabled })

    // Observer should not have been created
    expect(mockObserve).not.toHaveBeenCalled()
  })

  it('disconnects on unmount', () => {
    const sentinel = ref(document.createElement('div'))
    const callback = vi.fn()

    useInfiniteScroll(sentinel, callback)

    expect(mockObserve).toHaveBeenCalled()

    // Simulate unmount
    unmountCallbacks.forEach((cb) => cb())

    expect(mockDisconnect).toHaveBeenCalled()
  })
})
