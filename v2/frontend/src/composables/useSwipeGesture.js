import { ref, onMounted, onUnmounted } from 'vue'

export function useSwipeGesture(elementRef, { onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, threshold = 100 } = {}) {
  const offsetX = ref(0)
  const offsetY = ref(0)
  const isSwiping = ref(false)
  const swipeDirection = ref(null)

  let startX = 0
  let startY = 0
  let lockedAxis = null // 'horizontal' | 'vertical' | null
  let mouseDown = false

  function handleStart(clientX, clientY) {
    startX = clientX
    startY = clientY
    lockedAxis = null
    isSwiping.value = true
    offsetX.value = 0
    offsetY.value = 0
    swipeDirection.value = null
  }

  function handleMove(clientX, clientY, e) {
    if (!isSwiping.value) return
    const dx = clientX - startX
    const dy = clientY - startY

    // Lock axis once user moves > 10px in one direction
    if (!lockedAxis) {
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
        lockedAxis = Math.abs(dx) >= Math.abs(dy) ? 'horizontal' : 'vertical'
      } else {
        return
      }
    }

    if (lockedAxis === 'horizontal') {
      offsetX.value = dx
      offsetY.value = 0
      swipeDirection.value = dx > 30 ? 'right' : dx < -30 ? 'left' : null
    } else {
      offsetX.value = 0
      if (onSwipeDown) {
        // Allow both directions when onSwipeDown is provided
        offsetY.value = dy
        swipeDirection.value = dy < -30 ? 'up' : dy > 30 ? 'down' : null
      } else {
        // Only allow upward when no onSwipeDown handler
        offsetY.value = Math.min(dy, 0)
        swipeDirection.value = dy < -30 ? 'up' : null
      }
    }

    if (e) e.preventDefault()
  }

  function handleEnd() {
    if (!isSwiping.value) return

    if (lockedAxis === 'horizontal' && offsetX.value > threshold && onSwipeRight) {
      onSwipeRight()
    } else if (lockedAxis === 'horizontal' && offsetX.value < -threshold && onSwipeLeft) {
      onSwipeLeft()
    } else if (lockedAxis === 'vertical' && offsetY.value < -threshold && onSwipeUp) {
      onSwipeUp()
    } else if (lockedAxis === 'vertical' && offsetY.value > threshold && onSwipeDown) {
      onSwipeDown()
    }

    offsetX.value = 0
    offsetY.value = 0
    isSwiping.value = false
    swipeDirection.value = null
    lockedAxis = null
  }

  // Touch events
  function onTouchStart(e) {
    handleStart(e.touches[0].clientX, e.touches[0].clientY)
  }
  function onTouchMove(e) {
    handleMove(e.touches[0].clientX, e.touches[0].clientY, e)
  }
  function onTouchEnd() {
    handleEnd()
  }

  // Mouse events (for desktop / dev tools without touch emulation)
  function onMouseDown(e) {
    mouseDown = true
    handleStart(e.clientX, e.clientY)
  }
  function onMouseMove(e) {
    if (!mouseDown) return
    handleMove(e.clientX, e.clientY, e)
  }
  function onMouseUp() {
    if (!mouseDown) return
    mouseDown = false
    handleEnd()
  }

  onMounted(() => {
    const el = elementRef.value
    if (!el) return
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd)
    el.addEventListener('mousedown', onMouseDown)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  })

  onUnmounted(() => {
    const el = elementRef.value
    if (!el) return
    el.removeEventListener('touchstart', onTouchStart)
    el.removeEventListener('touchmove', onTouchMove)
    el.removeEventListener('touchend', onTouchEnd)
    el.removeEventListener('mousedown', onMouseDown)
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  })

  return { offsetX, offsetY, isSwiping, swipeDirection }
}
