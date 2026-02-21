<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionGroupStore } from '../../stores/transactionGroups'
import { useTransactionStore } from '../../stores/transactions'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const { t } = useI18n()
const groupStore = useTransactionGroupStore()
const transactionStore = useTransactionStore()

const props = defineProps({
  visible: Boolean,
  group: { type: Object, default: null },
  initialTransaction: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'saved', 'deleted'])

const name = ref('')
const linkedTransactions = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)

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
    searchResults.value = []
  }
}, { immediate: true })

const linkedIds = computed(() => new Set(linkedTransactions.value.map((t) => t.id)))

const outgoing = computed(() => linkedTransactions.value.filter((t) => t.id_source != null))
const incoming = computed(() => linkedTransactions.value.filter((t) => t.id_source == null))

const totalPaid = computed(() => outgoing.value.reduce((sum, t) => sum + parseFloat(t.amount), 0))
const totalReimbursed = computed(() => incoming.value.reduce((sum, t) => sum + parseFloat(t.amount), 0))
const netExpense = computed(() => totalPaid.value - totalReimbursed.value)

const ratio = computed(() => (totalPaid.value > 0 ? totalReimbursed.value / totalPaid.value : 0))

function previewEffective(tx) {
  if (tx.id_source != null) {
    return (parseFloat(tx.amount) * (1 - ratio.value)).toFixed(2)
  }
  return '0.00'
}

let searchTimeout = null
watch(searchQuery, (val) => {
  clearTimeout(searchTimeout)
  if (val.length < 3) {
    searchResults.value = []
    return
  }
  searchTimeout = setTimeout(async () => {
    searching.value = true
    try {
      const params = { search_query: val, start: 0, count: 10 }
      await transactionStore.fetchTransactions(params)
      searchResults.value = transactionStore.transactions.filter((t) => !linkedIds.value.has(t.id))
    } finally {
      searching.value = false
    }
  }, 400)
})

function addTransaction(tx) {
  if (!linkedIds.value.has(tx.id)) {
    linkedTransactions.value.push(tx)
  }
  searchQuery.value = ''
  searchResults.value = []
}

function removeTransaction(txId) {
  linkedTransactions.value = linkedTransactions.value.filter((t) => t.id !== txId)
}

async function save() {
  const payload = {
    name: name.value || null,
    transaction_ids: linkedTransactions.value.map((t) => t.id),
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

function isOutgoing(tx) {
  return tx.id_source != null
}
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="close"
    :header="group ? t('transactions.group') : t('transactions.createGroup')"
    modal
    :style="{ width: '600px' }"
    :closable="true"
  >
    <!-- Name -->
    <div class="mb-4">
      <label class="block text-sm font-medium mb-1">{{ t('transactions.groupName') }}</label>
      <InputText v-model="name" class="w-full" />
    </div>

    <!-- Linked transactions -->
    <div class="mb-4">
      <h3 class="text-sm font-medium mb-2">{{ t('transactions.title') }}</h3>
      <div v-if="linkedTransactions.length === 0" class="text-surface-400 text-sm py-2">
        {{ t('common.noResults') }}
      </div>
      <div v-else class="space-y-2 max-h-48 overflow-y-auto">
        <div
          v-for="tx in linkedTransactions"
          :key="tx.id"
          class="flex items-center justify-between bg-surface-50 rounded-lg px-3 py-2 text-sm"
        >
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <span :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'" class="font-bold text-xs">
              {{ isOutgoing(tx) ? '↓' : '↑' }}
            </span>
            <span class="truncate">{{ tx.description || '—' }}</span>
            <span class="text-surface-400 text-xs shrink-0">{{ tx.date }}</span>
            <span :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'" class="font-medium shrink-0">
              {{ tx.amount }}
            </span>
            <span class="text-surface-400 text-xs shrink-0">
              → {{ previewEffective(tx) }}
            </span>
          </div>
          <Button
            icon="pi pi-times"
            severity="danger"
            text
            size="small"
            @click="removeTransaction(tx.id)"
            :aria-label="t('transactions.removeFromGroup')"
          />
        </div>
      </div>
    </div>

    <!-- Search to add -->
    <div class="mb-4">
      <label class="block text-sm font-medium mb-1">{{ t('transactions.addToGroup') }}</label>
      <InputText v-model="searchQuery" :placeholder="t('common.search')" class="w-full" />
      <div v-if="searchResults.length > 0" class="mt-2 space-y-1 max-h-36 overflow-y-auto">
        <div
          v-for="tx in searchResults"
          :key="tx.id"
          class="flex items-center justify-between bg-surface-50 rounded px-3 py-1 text-sm cursor-pointer hover:bg-surface-100"
          @click="addTransaction(tx)"
        >
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <span :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'" class="font-bold text-xs">
              {{ isOutgoing(tx) ? '↓' : '↑' }}
            </span>
            <span class="truncate">{{ tx.description || '—' }}</span>
            <span class="text-surface-400 text-xs shrink-0">{{ tx.date }}</span>
            <span :class="isOutgoing(tx) ? 'text-red-500' : 'text-green-600'" class="font-medium shrink-0">
              {{ tx.amount }}
            </span>
          </div>
          <i class="pi pi-plus text-primary-500 text-xs" />
        </div>
      </div>
    </div>

    <!-- Summary -->
    <div class="bg-surface-50 rounded-lg p-3 mb-4">
      <h3 class="text-sm font-medium mb-2">{{ t('transactions.groupSummary') }}</h3>
      <div class="grid grid-cols-3 gap-2 text-sm">
        <div>
          <span class="text-surface-500">{{ t('transactions.totalPaid') }}</span>
          <div class="font-medium text-red-500">{{ totalPaid.toFixed(2) }}</div>
        </div>
        <div>
          <span class="text-surface-500">{{ t('transactions.totalReimbursed') }}</span>
          <div class="font-medium text-green-600">{{ totalReimbursed.toFixed(2) }}</div>
        </div>
        <div>
          <span class="text-surface-500">{{ t('transactions.netExpense') }}</span>
          <div class="font-bold">{{ netExpense.toFixed(2) }}</div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-between">
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
