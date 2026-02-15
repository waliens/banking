import { ref, computed } from 'vue'

export function usePagination(defaultPageSize = 50) {
  const page = ref(0)
  const pageSize = ref(defaultPageSize)
  const totalRecords = ref(0)

  const start = computed(() => page.value * pageSize.value)
  const totalPages = computed(() => Math.ceil(totalRecords.value / pageSize.value))

  function onPage(event) {
    page.value = event.page
    pageSize.value = event.rows
  }

  function reset() {
    page.value = 0
  }

  return { page, pageSize, totalRecords, start, totalPages, onPage, reset }
}
