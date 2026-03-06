import { watch, onUnmounted } from 'vue'

export function useInfiniteScroll(sentinelRef, callback, { rootMargin = '400px', enabled, root } = {}) {
  let observer = null
  let loading = false

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
      async (entries) => {
        if (entries[0].isIntersecting && !loading) {
          loading = true
          try {
            await callback()
          } finally {
            loading = false
          }
        }
      },
      { rootMargin, root: root?.value || null },
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
