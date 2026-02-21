import { watch, onUnmounted } from 'vue'

export function useInfiniteScroll(sentinelRef, callback, { rootMargin = '400px', enabled } = {}) {
  let observer = null

  function cleanup() {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  function setup() {
    cleanup()
    const el = sentinelRef.value
    if (!el) return
    if (enabled && !enabled.value) return

    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          callback()
        }
      },
      { rootMargin },
    )
    observer.observe(el)
  }

  watch(
    () => sentinelRef.value,
    () => setup(),
    { immediate: true },
  )

  if (enabled) {
    watch(enabled, (val) => {
      if (val) setup()
      else cleanup()
    })
  }

  onUnmounted(cleanup)
}
