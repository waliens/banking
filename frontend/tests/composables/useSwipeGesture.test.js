import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useSwipeGesture } from '../../src/composables/useSwipeGesture'

function touch(x, y) {
  return { touches: [{ clientX: x, clientY: y }] }
}

describe('useSwipeGesture', () => {
  function makeComponent(opts) {
    // Use dynamic import to avoid hoisting issues
    return import('@vue/test-utils').then(({ mount }) =>
      import('vue').then(({ defineComponent, ref: vueRef }) => {
        const TestComp = defineComponent({
          setup() {
            const cardRef = vueRef(null)
            const result = useSwipeGesture(cardRef, opts)
            return { cardRef, ...result }
          },
          template: '<div ref="cardRef" />',
        })
        return mount(TestComp)
      }),
    )
  }

  function simulateSwipe(div, startX, startY, endX, endY, steps = 5) {
    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: startX, clientY: startY })] }))
    for (let i = 1; i <= steps; i++) {
      const x = startX + (endX - startX) * (i / steps)
      const y = startY + (endY - startY) * (i / steps)
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: x, clientY: y })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))
  }

  it('registers touch event listeners on mount', async () => {
    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeRight: onRight,
      onSwipeLeft: onLeft,
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    simulateSwipe(wrapper.element, 0, 100, 100, 100)

    expect(onRight).toHaveBeenCalled()
    expect(onLeft).not.toHaveBeenCalled()
    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('fires onSwipeLeft for negative horizontal swipe', async () => {
    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeRight: onRight,
      onSwipeLeft: onLeft,
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    simulateSwipe(wrapper.element, 200, 100, 100, 100)

    expect(onLeft).toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('fires onSwipeUp for negative vertical swipe', async () => {
    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeRight: onRight,
      onSwipeLeft: onLeft,
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    simulateSwipe(wrapper.element, 100, 200, 100, 100)

    expect(onUp).toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()
    expect(onLeft).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('locks to horizontal axis and ignores vertical movement', async () => {
    const onRight = vi.fn()
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeRight: onRight,
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    const div = wrapper.element

    // Start, then move horizontally to lock axis, then add vertical component
    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 0, clientY: 100 })] }))
    // First move: horizontal to lock axis
    div.dispatchEvent(new TouchEvent('touchmove', {
      touches: [new Touch({ identifier: 0, target: div, clientX: 20, clientY: 100 })],
      cancelable: true,
    }))
    // Continue with diagonal movement — should stay horizontal locked
    for (let i = 2; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: i * 20, clientY: 100 - i * 20 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onRight).toHaveBeenCalled()
    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('fires onSwipeDown for positive vertical swipe when handler provided', async () => {
    const onUp = vi.fn()
    const onDown = vi.fn()

    const wrapper = await makeComponent({
      onSwipeUp: onUp,
      onSwipeDown: onDown,
      threshold: 50,
    })
    await nextTick()

    simulateSwipe(wrapper.element, 100, 100, 100, 200)

    expect(onDown).toHaveBeenCalled()
    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('clamps vertical to upward-only when no onSwipeDown handler', async () => {
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    // Swipe down — should NOT fire onUp
    simulateSwipe(wrapper.element, 100, 100, 100, 200)

    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('locks to vertical axis and ignores horizontal movement', async () => {
    const onRight = vi.fn()
    const onUp = vi.fn()

    const wrapper = await makeComponent({
      onSwipeRight: onRight,
      onSwipeUp: onUp,
      threshold: 50,
    })
    await nextTick()

    const div = wrapper.element

    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 200 })] }))
    // First move: vertical to lock axis
    div.dispatchEvent(new TouchEvent('touchmove', {
      touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 180 })],
      cancelable: true,
    }))
    // Continue with diagonal movement — should stay vertical locked
    for (let i = 2; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: 100 + i * 20, clientY: 200 - i * 20 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onUp).toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()

    wrapper.unmount()
  })
})
