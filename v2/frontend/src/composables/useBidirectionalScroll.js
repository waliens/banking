import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

/**
 * Composable for bidirectional infinite scroll using IntersectionObserver.
 *
 * @param {import('vue').Ref<HTMLElement|null>} topSentinel - Ref to the top sentinel element
 * @param {import('vue').Ref<HTMLElement|null>} bottomSentinel - Ref to the bottom sentinel element
 * @param {Object} options
 * @param {() => Promise<void>} options.onLoadBefore - Called when top sentinel becomes visible
 * @param {() => Promise<void>} options.onLoadAfter - Called when bottom sentinel becomes visible
 * @param {import('vue').Ref<HTMLElement|null>} [options.root] - Scroll container (default: null = viewport)
 */
export function useBidirectionalScroll(topSentinel, bottomSentinel, { onLoadBefore, onLoadAfter, root }) {
  const loadingBefore = ref(false)
  const loadingAfter = ref(false)

  let topObserver = null
  let bottomObserver = null

  function createObservers() {
    destroyObservers()

    const observerOptions = {
      root: root?.value || null,
      rootMargin: '400px',
      threshold: 0,
    }

    topObserver = new IntersectionObserver(async (entries) => {
      if (entries[0].isIntersecting && !loadingBefore.value) {
        loadingBefore.value = true
        try {
          await onLoadBefore()
        } finally {
          loadingBefore.value = false
        }
      }
    }, observerOptions)

    bottomObserver = new IntersectionObserver(async (entries) => {
      if (entries[0].isIntersecting && !loadingAfter.value) {
        loadingAfter.value = true
        try {
          await onLoadAfter()
        } finally {
          loadingAfter.value = false
        }
      }
    }, observerOptions)

    if (topSentinel.value) topObserver.observe(topSentinel.value)
    if (bottomSentinel.value) bottomObserver.observe(bottomSentinel.value)
  }

  function destroyObservers() {
    topObserver?.disconnect()
    bottomObserver?.disconnect()
    topObserver = null
    bottomObserver = null
  }

  // Watch for sentinel elements becoming available (v-if / nextTick)
  watch([topSentinel, bottomSentinel], () => {
    createObservers()
  })

  onMounted(() => {
    createObservers()
  })

  onBeforeUnmount(() => {
    destroyObservers()
  })

  return { loadingBefore, loadingAfter }
}
