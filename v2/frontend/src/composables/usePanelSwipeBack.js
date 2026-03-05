import { ref, watch, onUnmounted } from 'vue'

/**
 * Composable for swipe-to-go-back gesture on panels.
 *
 * For left panels (opened by swiping left): swipe right to go back.
 * For bottom panels (opened by swiping down): swipe up to go back.
 *
 * Scroll-aware: vertical swipe-back only triggers when content is scrolled to the top.
 * Horizontal swipe-back works regardless of scroll position (axis-locked, no conflict).
 *
 * @param {Ref<HTMLElement>} containerRef - ref to the scrollable container
 * @param {Object} options
 * @param {Function} options.onBack - called when swipe-back gesture completes
 * @param {'right'|'up'} options.direction - 'right' for left panels, 'up' for bottom panels
 * @param {number} options.threshold - minimum pixels to trigger (default: 80)
 * @returns {{ offset: Ref<number>, active: Ref<boolean> }}
 */
export function usePanelSwipeBack(containerRef, { onBack, direction = 'right', threshold = 80 } = {}) {
  const offset = ref(0)
  const active = ref(false)

  let startX = 0
  let startY = 0
  let lockedAxis = null
  let shouldIntercept = false
  let initialScrollTop = 0
  let currentEl = null

  function onTouchStart(e) {
    const touch = e.touches[0]
    startX = touch.clientX
    startY = touch.clientY
    lockedAxis = null
    shouldIntercept = false
    offset.value = 0
    active.value = false

    const el = containerRef.value
    initialScrollTop = el ? el.scrollTop : 0
  }

  function onTouchMove(e) {
    const touch = e.touches[0]
    const dx = touch.clientX - startX
    const dy = touch.clientY - startY

    if (!lockedAxis) {
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
        lockedAxis = Math.abs(dx) >= Math.abs(dy) ? 'horizontal' : 'vertical'

        if (direction === 'right' && lockedAxis === 'horizontal' && dx > 0) {
          shouldIntercept = true
        } else if (direction === 'up' && lockedAxis === 'vertical' && dy > 0 && initialScrollTop <= 0) {
          // Pulling content down when already at scroll top = dismiss bottom panel
          shouldIntercept = true
        }

        if (!shouldIntercept) return
      } else {
        return
      }
    }

    if (!shouldIntercept) return

    e.preventDefault()
    active.value = true

    if (direction === 'right') {
      offset.value = Math.max(0, dx)
    } else if (direction === 'up') {
      // dy > 0 means finger moved down = pulling content down to dismiss
      offset.value = Math.max(0, dy)
    }
  }

  function onTouchEnd() {
    if (shouldIntercept && offset.value > threshold) {
      onBack()
    }
    offset.value = 0
    active.value = false
    lockedAxis = null
    shouldIntercept = false
  }

  function attach(el) {
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd)
    currentEl = el
  }

  function detach(el) {
    el.removeEventListener('touchstart', onTouchStart)
    el.removeEventListener('touchmove', onTouchMove)
    el.removeEventListener('touchend', onTouchEnd)
    currentEl = null
  }

  watch(containerRef, (newEl, oldEl) => {
    if (oldEl) detach(oldEl)
    if (newEl) attach(newEl)
  }, { immediate: true, flush: 'post' })

  onUnmounted(() => {
    if (currentEl) detach(currentEl)
  })

  return { offset, active }
}
