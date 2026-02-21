import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useSwipeGesture } from '../../src/composables/useSwipeGesture'

function createMockElement() {
  const listeners = {}
  return {
    addEventListener: vi.fn((event, handler) => {
      listeners[event] = handler
    }),
    removeEventListener: vi.fn(),
    _listeners: listeners,
    _fire(event, data) {
      if (listeners[event]) listeners[event](data)
    },
  }
}

function touch(x, y) {
  return { touches: [{ clientX: x, clientY: y }] }
}

describe('useSwipeGesture', () => {
  let el, elementRef, callbacks

  beforeEach(() => {
    el = createMockElement()
    elementRef = ref(el)
    callbacks = {
      onSwipeLeft: vi.fn(),
      onSwipeRight: vi.fn(),
      onSwipeUp: vi.fn(),
      threshold: 100,
    }
  })

  function setup(opts = callbacks) {
    // Manually simulate onMounted by calling the composable then triggering listeners
    const result = { offsetX: ref(0), offsetY: ref(0), isSwiping: ref(false), swipeDirection: ref(null) }

    // We need to call onMounted hooks — mount a minimal component
    // Instead, let's directly test the logic by simulating touch events on the element
    // The composable attaches listeners in onMounted, so we replicate that
    const { offsetX, offsetY, isSwiping, swipeDirection } = useSwipeGesture.__test
      ? useSwipeGesture(elementRef, opts)
      : (() => {
          // Since onMounted won't fire outside a component, we manually attach
          const listeners = {}
          let startX = 0, startY = 0, lockedAxis = null
          const offsetX = ref(0), offsetY = ref(0), isSwiping = ref(false), swipeDirection = ref(null)

          el._fire('touchstart', touch(100, 100))
          // This won't work because onMounted hasn't fired.
          // Let's take a different approach.
          return { offsetX, offsetY, isSwiping, swipeDirection }
        })()

    return result
  }

  // Since useSwipeGesture uses onMounted/onUnmounted lifecycle hooks,
  // we test the logic by directly simulating the touch event flow.
  // We'll manually replicate what the composable does.

  function simulateSwipe(el, startX, startY, endX, endY) {
    el._fire('touchstart', { touches: [{ clientX: startX, clientY: startY }] })
    // Move in small steps
    const steps = 5
    for (let i = 1; i <= steps; i++) {
      const x = startX + (endX - startX) * (i / steps)
      const y = startY + (endY - startY) * (i / steps)
      const event = {
        touches: [{ clientX: x, clientY: y }],
        preventDefault: vi.fn(),
      }
      el._fire('touchmove', event)
    }
    el._fire('touchend', {})
  }

  it('registers touch event listeners on mount', async () => {
    // We need a component context for onMounted. Use a minimal wrapper.
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        const result = useSwipeGesture(cardRef, {
          onSwipeRight: onRight,
          onSwipeLeft: onLeft,
          onSwipeUp: onUp,
          threshold: 50,
        })
        return { cardRef, ...result }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
    const div = wrapper.element

    // Simulate swipe right (> threshold)
    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 0, clientY: 100 })] }))
    for (let i = 1; i <= 5; i++) {
      const evt = new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: i * 20, clientY: 100 })],
        cancelable: true,
      })
      div.dispatchEvent(evt)
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onRight).toHaveBeenCalled()
    expect(onLeft).not.toHaveBeenCalled()
    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('fires onSwipeLeft for negative horizontal swipe', async () => {
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        useSwipeGesture(cardRef, { onSwipeRight: onRight, onSwipeLeft: onLeft, onSwipeUp: onUp, threshold: 50 })
        return { cardRef }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
    const div = wrapper.element

    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 200, clientY: 100 })] }))
    for (let i = 1; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: 200 - i * 20, clientY: 100 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onLeft).toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('fires onSwipeUp for negative vertical swipe', async () => {
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onRight = vi.fn()
    const onLeft = vi.fn()
    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        useSwipeGesture(cardRef, { onSwipeRight: onRight, onSwipeLeft: onLeft, onSwipeUp: onUp, threshold: 50 })
        return { cardRef }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
    const div = wrapper.element

    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 200 })] }))
    for (let i = 1; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 200 - i * 20 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onUp).toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()
    expect(onLeft).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('locks to horizontal axis and ignores vertical movement', async () => {
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onRight = vi.fn()
    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        const result = useSwipeGesture(cardRef, { onSwipeRight: onRight, onSwipeUp: onUp, threshold: 50 })
        return { cardRef, ...result }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
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
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onUp = vi.fn()
    const onDown = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        useSwipeGesture(cardRef, { onSwipeUp: onUp, onSwipeDown: onDown, threshold: 50 })
        return { cardRef }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
    const div = wrapper.element

    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 100 })] }))
    for (let i = 1; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 100 + i * 20 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onDown).toHaveBeenCalled()
    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('clamps vertical to upward-only when no onSwipeDown handler', async () => {
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        const result = useSwipeGesture(cardRef, { onSwipeUp: onUp, threshold: 50 })
        return { cardRef, ...result }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
    const div = wrapper.element

    // Swipe down — should NOT fire onUp and offset should be clamped to 0
    div.dispatchEvent(new TouchEvent('touchstart', { touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 100 })] }))
    for (let i = 1; i <= 5; i++) {
      div.dispatchEvent(new TouchEvent('touchmove', {
        touches: [new Touch({ identifier: 0, target: div, clientX: 100, clientY: 100 + i * 20 })],
        cancelable: true,
      }))
    }
    div.dispatchEvent(new TouchEvent('touchend', { touches: [] }))

    expect(onUp).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('locks to vertical axis and ignores horizontal movement', async () => {
    const { mount } = await import('@vue/test-utils')
    const { defineComponent, ref: vueRef } = await import('vue')

    const onRight = vi.fn()
    const onUp = vi.fn()

    const TestComp = defineComponent({
      setup() {
        const cardRef = vueRef(null)
        useSwipeGesture(cardRef, { onSwipeRight: onRight, onSwipeUp: onUp, threshold: 50 })
        return { cardRef }
      },
      template: '<div ref="cardRef" />',
    })

    const wrapper = mount(TestComp)
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
