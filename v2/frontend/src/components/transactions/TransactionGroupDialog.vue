<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionGroupStore } from '../../stores/transactionGroups'
import { useBidirectionalScroll } from '../../composables/useBidirectionalScroll'
import api from '../../services/api'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const PAGE_SIZE = 25

const { t } = useI18n()
const groupStore = useTransactionGroupStore()

const props = defineProps({
  visible: Boolean,
  group: { type: Object, default: null },
  initialTransaction: { type: Object, default: null },
  walletId: { type: Number, default: null },
  walletAccountIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'saved', 'deleted'])

const name = ref('')
const linkedTransactions = ref([])
const searchQuery = ref('')

// Timeline state — single list, newest first (date DESC)
// Two independent paginated streams: "older" (date <= anchor) and "newer" (date > anchor)
// Each uses offset-based pagination against the /transactions endpoint
const anchorDate = ref(null)
const items = ref([])          // older items (anchor date and before), newest first
const newerItems = ref([])     // newer items (after anchor date), newest first
const olderOffset = ref(0)
const newerOffset = ref(0)
const hasMoreOlder = ref(true)
const hasMoreNewer = ref(true)

// Sentinel refs for infinite scroll
const topSentinelRef = ref(null)
const bottomSentinelRef = ref(null)
const scrollContainerRef = ref(null)

const linkedIds = computed(() => new Set(linkedTransactions.value.map((t) => t.id)))

// Combined list: newer (newest first) then older (newest first) = full timeline newest first
const allTimelineItems = computed(() => [...newerItems.value, ...items.value])

// Group by date for display
const groupedTimeline = computed(() => {
  const groups = []
  let currentDate = null
  let currentGroup = null
  for (const tx of allTimelineItems.value) {
    if (tx.date !== currentDate) {
      currentDate = tx.date
      currentGroup = { date: tx.date, transactions: [] }
      groups.push(currentGroup)
    }
    currentGroup.transactions.push(tx)
  }
  return groups
})

function isOutgoing(tx) {
  return props.walletAccountIds.includes(tx.id_source)
}

const outgoing = computed(() => linkedTransactions.value.filter((t) => isOutgoing(t)))
const incoming = computed(() => linkedTransactions.value.filter((t) => !isOutgoing(t)))

const totalPaid = computed(() => outgoing.value.reduce((sum, t) => sum + parseFloat(t.amount), 0))
const totalReimbursed = computed(() => incoming.value.reduce((sum, t) => sum + parseFloat(t.amount), 0))
const netExpense = computed(() => totalPaid.value - totalReimbursed.value)

const ratio = computed(() => (totalPaid.value > 0 ? totalReimbursed.value / totalPaid.value : 0))

function previewEffective(tx) {
  if (isOutgoing(tx)) {
    return (parseFloat(tx.amount) * (1 - ratio.value)).toFixed(2)
  }
  return '0.00'
}

function buildParams(extra = {}) {
  const params = {
    wallet: props.walletId,
    wallet_external_only: true,
    count: PAGE_SIZE,
    duplicate_only: false,
    exclude_grouped: true,
    ...extra,
  }
  if (searchQuery.value) {
    params.search_query = searchQuery.value
  }
  return params
}

// Helper: get the next calendar day as YYYY-MM-DD string
function nextDay(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d + 1))
  return date.toISOString().slice(0, 10)
}

// Load older transactions (anchor date and before, date DESC, offset-based)
let loadingOlder = false
async function loadOlder() {
  if (!hasMoreOlder.value || loadingOlder) return
  loadingOlder = true
  try {
    const { data } = await api.get('/transactions', {
      params: buildParams({ date_to: anchorDate.value, order: 'desc', start: olderOffset.value }),
    })
    if (data.length > 0) {
      items.value = [...items.value, ...data]
      olderOffset.value += data.length
    }
    hasMoreOlder.value = data.length === PAGE_SIZE
  } finally {
    loadingOlder = false
  }
}

// Load newer transactions (strictly after anchor date, date ASC then reversed)
let loadingNewer = false
async function loadNewer() {
  if (!hasMoreNewer.value || loadingNewer) return
  loadingNewer = true
  try {
    const { data } = await api.get('/transactions', {
      params: buildParams({ date_from: nextDay(anchorDate.value), order: 'asc', start: newerOffset.value }),
    })
    if (data.length > 0) {
      // data is date ASC; reverse so newest is first, then prepend
      // (later pages have more recent items that belong at the top)
      newerItems.value = [...data.reverse(), ...newerItems.value]
      newerOffset.value += data.length
    }
    hasMoreNewer.value = data.length === PAGE_SIZE
  } finally {
    loadingNewer = false
  }
}

async function initialLoad() {
  items.value = []
  newerItems.value = []
  olderOffset.value = 0
  newerOffset.value = 0
  hasMoreOlder.value = true
  hasMoreNewer.value = true

  // Load anchor date and older, then newer
  await loadOlder()
  await loadNewer()

  // When editing an existing group, inject its transactions back
  // (they were excluded by exclude_grouped filter)
  if (props.group?.transactions) {
    const existingIds = new Set(allTimelineItems.value.map((t) => t.id))
    const toInject = props.group.transactions.filter((tx) => !existingIds.has(tx.id))
    for (const tx of toInject) {
      if (tx.date > anchorDate.value) {
        newerItems.value.push(tx)
      } else {
        items.value.push(tx)
      }
    }
    if (toInject.length > 0) {
      // Re-sort both arrays: newest first
      items.value.sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id)
      newerItems.value.sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id)
    }
  }

  // Scroll to anchor transaction
  await nextTick()
  if (props.initialTransaction && scrollContainerRef.value) {
    const el = scrollContainerRef.value.querySelector(`[data-tx-id="${props.initialTransaction.id}"]`)
    if (el) {
      el.scrollIntoView({ block: 'center' })
    }
  }
}

// Setup bidirectional scroll
useBidirectionalScroll(topSentinelRef, bottomSentinelRef, {
  onLoadBefore: loadNewer,   // top sentinel = load more future (newer)
  onLoadAfter: loadOlder,    // bottom sentinel = load more past (older)
  root: scrollContainerRef,
})

// Debounced search
let searchTimeout = null
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    initialLoad()
  }, 400)
})

// Dialog open/close
watch(() => props.visible, (val) => {
  if (val) {
    if (props.group) {
      name.value = props.group.name || ''
      linkedTransactions.value = [...props.group.transactions]
    } else {
      name.value = ''
      linkedTransactions.value = props.initialTransaction ? [props.initialTransaction] : []
    }
    searchQuery.value = ''
    anchorDate.value = props.initialTransaction?.date || new Date().toISOString().slice(0, 10)
    initialLoad()
  }
}, { immediate: true })

function toggleTransaction(tx) {
  if (linkedIds.value.has(tx.id)) {
    linkedTransactions.value = linkedTransactions.value.filter((t) => t.id !== tx.id)
  } else {
    linkedTransactions.value.push(tx)
  }
}

function removeTransaction(txId) {
  linkedTransactions.value = linkedTransactions.value.filter((t) => t.id !== txId)
}

function isAnchorTransaction(tx) {
  return props.initialTransaction && tx.id === props.initialTransaction.id
}

async function save() {
  const payload = {
    name: name.value || null,
    transaction_ids: linkedTransactions.value.map((t) => t.id),
    wallet_id: props.walletId,
  }
  if (props.group) {
    await groupStore.updateGroup(props.group.id, payload)
  } else {
    await groupStore.createGroup(payload)
  }
  emit('saved')
  emit('update:visible', false)
}

async function deleteGroup() {
  if (!props.group) return
  await groupStore.deleteGroup(props.group.id)
  emit('deleted')
  emit('update:visible', false)
}

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="close"
    :header="group ? t('transactions.group') : t('transactions.createGroup')"
    modal
    :style="{ width: '700px' }"
    :closable="true"
  >
    <!-- Name -->
    <div class="mb-4">
      <label class="block text-sm font-medium mb-1">{{ t('transactions.groupName') }}</label>
      <InputText v-model="name" class="w-full" />
    </div>

    <!-- Two-panel layout -->
    <div class="flex gap-4" style="min-height: 400px">
      <!-- Left panel: Available transactions timeline -->
      <div class="flex-1 flex flex-col min-w-0 border border-surface-200 rounded-lg">
        <div class="px-3 py-2 border-b border-surface-200">
          <h3 class="text-sm font-medium mb-1">{{ t('transactionDetail.availableTransactions') }}</h3>
          <InputText
            v-model="searchQuery"
            :placeholder="t('common.search')"
            class="w-full"
            size="small"
          />
        </div>

        <div
          ref="scrollContainerRef"
          class="flex-1 overflow-y-auto"
          style="max-height: 350px"
        >
          <!-- Top sentinel (load more future) -->
          <div ref="topSentinelRef" class="h-1" />

          <div v-if="allTimelineItems.length === 0" class="text-surface-400 text-sm py-4 text-center">
            {{ t('common.noResults') }}
          </div>

          <template v-for="dateGroup in groupedTimeline" :key="dateGroup.date">
            <!-- Date header -->
            <div
              class="sticky top-0 bg-surface-50 px-3 py-1 text-xs font-semibold text-surface-500 border-b border-surface-100"
              :class="{ 'bg-primary-50 text-primary-700': dateGroup.date === anchorDate }"
            >
              {{ dateGroup.date }}
              <span v-if="dateGroup.date === anchorDate" class="ml-1">&#8592;</span>
            </div>

            <div
              v-for="tx in dateGroup.transactions"
              :key="tx.id"
              :data-tx-id="tx.id"
              class="flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer hover:bg-surface-50 border-b border-surface-50"
              :class="{
                'bg-primary-50': linkedIds.has(tx.id),
                'bg-amber-50 font-semibold': isAnchorTransaction(tx),
              }"
              @click="toggleTransaction(tx)"
            >
              <span
                :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'"
                class="font-bold text-xs w-4 text-center shrink-0"
              >
                {{ isOutgoing(tx) ? '↓' : '↑' }}
              </span>
              <span v-if="isAnchorTransaction(tx)" class="text-amber-500 text-xs shrink-0">&#9733;</span>
              <span class="truncate flex-1 min-w-0">{{ tx.description || '—' }}</span>
              <span
                :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'"
                class="font-medium shrink-0 text-xs"
              >
                {{ tx.amount }}
              </span>
              <i
                v-if="linkedIds.has(tx.id)"
                class="pi pi-check text-primary-500 text-xs shrink-0"
              />
            </div>
          </template>

          <!-- Bottom sentinel (load more past) -->
          <div ref="bottomSentinelRef" class="h-1" />
        </div>
      </div>

      <!-- Right panel: Linked transactions + summary -->
      <div class="w-56 flex flex-col shrink-0">
        <h3 class="text-sm font-medium mb-2">{{ t('transactions.title') }}</h3>

        <div v-if="linkedTransactions.length === 0" class="text-surface-400 text-sm py-2">
          {{ t('common.noResults') }}
        </div>

        <div v-else class="space-y-1 flex-1 overflow-y-auto max-h-48">
          <div
            v-for="tx in linkedTransactions"
            :key="tx.id"
            class="flex items-center gap-1 bg-surface-50 rounded px-2 py-1 text-xs"
          >
            <span
              :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'"
              class="font-bold shrink-0"
            >
              {{ isOutgoing(tx) ? '↓' : '↑' }}
            </span>
            <span class="truncate flex-1 min-w-0">{{ tx.description || '—' }}</span>
            <span
              :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'"
              class="font-medium shrink-0"
            >
              {{ tx.amount }}
            </span>
            <button
              class="text-red-400 hover:text-red-600 shrink-0 ml-1"
              @click="removeTransaction(tx.id)"
              :aria-label="t('transactions.removeFromGroup')"
            >
              <i class="pi pi-times text-xs" />
            </button>
          </div>
        </div>

        <!-- Warning: splits will be cleared -->
        <div
          v-if="linkedTransactions.some((tx) => tx.category_splits && tx.category_splits.length > 0)"
          class="bg-amber-50 border border-amber-200 rounded p-2 mt-2 text-xs text-amber-800"
        >
          <i class="pi pi-exclamation-triangle mr-1"></i>
          {{ t('transactionDetail.groupWillClearCategories') }}
        </div>

        <!-- Summary -->
        <div class="bg-surface-50 rounded p-2 mt-2">
          <h4 class="text-xs font-medium mb-1">{{ t('transactions.groupSummary') }}</h4>
          <div class="space-y-1 text-xs">
            <div class="flex justify-between">
              <span class="text-surface-500">{{ t('transactions.totalPaid') }}</span>
              <span class="font-medium text-red-500">{{ totalPaid.toFixed(2) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-500">{{ t('transactions.totalReimbursed') }}</span>
              <span class="font-medium text-green-600">{{ totalReimbursed.toFixed(2) }}</span>
            </div>
            <div class="flex justify-between border-t border-surface-200 pt-1">
              <span class="text-surface-500">{{ t('transactions.netExpense') }}</span>
              <span class="font-bold">{{ netExpense.toFixed(2) }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-between mt-4">
      <Button
        v-if="group"
        :label="t('common.delete')"
        severity="danger"
        text
        @click="deleteGroup"
      />
      <span v-else />
      <div class="flex gap-2">
        <Button :label="t('common.cancel')" severity="secondary" text @click="close" />
        <Button
          :label="t('common.save')"
          :disabled="linkedTransactions.length === 0"
          @click="save"
        />
      </div>
    </div>
  </Dialog>
</template>
