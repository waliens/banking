<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useDebounce } from '../../composables/useDebounce'
import api from '../../services/api'
import InputText from 'primevue/inputtext'
import AccountDisplay from './AccountDisplay.vue'

const PAGE_SIZE = 25

const props = defineProps({
  modelValue: {
    type: [Number, Array, null],
    default: null
  },
  placeholder: {
    type: String,
    default: 'Select account'
  },
  showClear: {
    type: Boolean,
    default: false
  },
  multiple: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const searchQuery = ref('')
const options = ref([])
const offset = ref(0)
const hasMore = ref(true)
const loadingMore = ref(false)
const selectedAccounts = ref(new Map())
const rootRef = ref(null)
const triggerRef = ref(null)
const dropdownRef = ref(null)
const dropdownStyle = ref({})

// Debounced search query
const debouncedQuery = useDebounce(searchQuery, 300)

// Display label for trigger button
const displayLabel = computed(() => {
  if (props.multiple) {
    const selected = Array.isArray(props.modelValue) ? props.modelValue : []
    if (selected.length === 0) return props.placeholder
    const accounts = selected.map(id => selectedAccounts.value.get(id)).filter(Boolean)
    return accounts.length > 0 ? `${accounts.length} account(s)` : props.placeholder
  } else {
    if (props.modelValue == null) return props.placeholder
    const account = selectedAccounts.value.get(props.modelValue)
    return account ? (account.name || account.number || '#' + account.id) : props.placeholder
  }
})

// Check if single account is selected
function isSelected(accountId) {
  if (props.multiple) {
    return Array.isArray(props.modelValue) && props.modelValue.includes(accountId)
  }
  return props.modelValue === accountId
}

// Fetch accounts from backend
async function fetchAccounts(reset = false) {
  if (reset) {
    offset.value = 0
    options.value = []
    hasMore.value = true
  }

  if (!hasMore.value || loadingMore.value) return

  loadingMore.value = true
  try {
    const params = { start: offset.value, count: PAGE_SIZE }
    if (debouncedQuery.value.trim()) {
      params.search = debouncedQuery.value.trim()
    }

    const { data } = await api.get('/accounts', { params })
    options.value = [...options.value, ...data]
    offset.value += data.length
    hasMore.value = data.length === PAGE_SIZE
  } catch (error) {
    console.error('Failed to fetch accounts:', error)
  } finally {
    loadingMore.value = false
  }
}

// Handle scroll in dropdown list
function onListScroll(event) {
  const el = event.currentTarget
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
    fetchAccounts()
  }
}

// Select/deselect account — toggles in multi-select mode
function selectAccount(account) {
  if (props.multiple) {
    const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    if (current.includes(account.id)) {
      emit('update:modelValue', current.filter(id => id !== account.id))
    } else {
      selectedAccounts.value.set(account.id, account)
      current.push(account.id)
      emit('update:modelValue', current)
    }
  } else {
    selectedAccounts.value.set(account.id, account)
    emit('update:modelValue', account.id)
    isOpen.value = false
  }
}

// Clear selection
function clearSelection() {
  if (props.multiple) {
    emit('update:modelValue', [])
  } else {
    emit('update:modelValue', null)
    isOpen.value = false
  }
  selectedAccounts.value.clear()
}

// Open dropdown — compute fixed position from trigger's bounding rect so it escapes any overflow
async function open() {
  isOpen.value = true
  searchQuery.value = ''
  await nextTick()
  if (triggerRef.value) {
    const rect = triggerRef.value.getBoundingClientRect()
    dropdownStyle.value = {
      top: `${rect.bottom + 4}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
    }
  }
  await fetchAccounts(true)
}

// Watch search query changes
watch(debouncedQuery, () => {
  if (isOpen.value) {
    fetchAccounts(true)
  }
})

// Fetch selected account(s) data when modelValue changes
watch(() => props.modelValue, async (val) => {
  const ids = Array.isArray(val) ? val : (val != null ? [val] : [])
  for (const id of ids) {
    if (!selectedAccounts.value.has(id)) {
      try {
        const { data } = await api.get(`/accounts/${id}`)
        selectedAccounts.value.set(id, data)
      } catch (error) {
        console.error(`Failed to fetch account ${id}:`, error)
      }
    }
  }
}, { immediate: true, deep: true })

// Click outside to close — must check both the trigger root and the teleported dropdown
function handleClickOutside(event) {
  if (
    rootRef.value && !rootRef.value.contains(event.target) &&
    (!dropdownRef.value || !dropdownRef.value.contains(event.target))
  ) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="rootRef" class="relative">
    <!-- Trigger button -->
    <button
      ref="triggerRef"
      @click="isOpen ? (isOpen = false) : open()"
      class="w-full flex items-center justify-between gap-2 px-3 py-2
             border border-surface-200 rounded-lg bg-surface-0 text-surface-900
             hover:border-surface-300 transition-colors cursor-pointer text-left text-sm"
    >
      <span class="truncate">{{ displayLabel }}</span>
      <div class="flex items-center gap-1 shrink-0">
        <button
          v-if="showClear && ((multiple && modelValue?.length > 0) || (!multiple && modelValue != null))"
          @click.stop="clearSelection"
          class="text-surface-400 hover:text-surface-600 transition-colors"
          type="button"
        >
          <i class="pi pi-times text-xs"></i>
        </button>
        <i class="pi pi-chevron-down text-xs text-surface-400"></i>
      </div>
    </button>

    <!-- Panel — teleported to body so it escapes Dialog overflow clipping -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="dropdownRef"
        :style="dropdownStyle"
        class="fixed z-[9999] min-w-48 bg-surface-0 border border-surface-200 rounded-lg shadow-xl overflow-hidden"
      >
        <!-- Search input -->
        <div class="p-2 border-b border-surface-100">
          <InputText
            v-model="searchQuery"
            placeholder="Search..."
            class="w-full text-sm"
            autofocus
          />
        </div>

        <!-- Scrollable list -->
        <div
          class="overflow-y-auto max-h-64"
          @scroll="onListScroll"
        >
          <!-- Accounts -->
          <div
            v-for="account in options"
            :key="account.id"
            @click="selectAccount(account)"
            class="flex items-center gap-2 px-3 py-2 hover:bg-surface-100
                   cursor-pointer text-sm transition-colors"
          >
            <!-- Checkbox indicator for multi-select -->
            <div v-if="multiple" class="w-4 shrink-0 flex items-center justify-center">
              <i v-if="isSelected(account.id)" class="pi pi-check text-primary-500 text-xs" />
            </div>

            <!-- Account info -->
            <AccountDisplay :account="account" class="min-w-0 flex-1 text-surface-900" />
          </div>

          <!-- Loading spinner -->
          <div v-if="loadingMore" class="px-3 py-2 text-xs text-surface-400 text-center">
            <i class="pi pi-spinner pi-spin"></i> Loading…
          </div>

          <!-- No results message -->
          <div
            v-if="!loadingMore && !hasMore && options.length === 0"
            class="px-3 py-2 text-xs text-surface-400 text-center"
          >
            No accounts found
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
