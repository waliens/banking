<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../../stores/transactions'
import Button from 'primevue/button'
import Tooltip from 'primevue/tooltip'
import AccountDisplay from '../common/AccountDisplay.vue'

const vTooltip = Tooltip

const props = defineProps({
  transactionId: { type: Number, required: true },
})

const emit = defineEmits(['resolved'])

const { t } = useI18n()
const transactionStore = useTransactionStore()

const candidates = ref([])
const loading = ref(false)

async function loadCandidates() {
  loading.value = true
  try {
    candidates.value = await transactionStore.fetchDuplicateCandidates(props.transactionId)
  } finally {
    loading.value = false
  }
}

async function markDuplicate(candidateId) {
  await transactionStore.markDuplicate(candidateId, props.transactionId)
  candidates.value = candidates.value.filter((c) => c.id !== candidateId)
  emit('resolved')
}

watch(() => props.transactionId, loadCandidates, { immediate: true })
</script>

<template>
  <div class="p-3 bg-surface-100 rounded-lg">
    <h4 class="text-sm font-semibold mb-2">{{ t('review.duplicateFound') }}</h4>

    <div v-if="loading" class="text-sm text-surface-500">{{ t('common.loading') }}</div>

    <div v-else-if="candidates.length === 0" class="text-sm text-surface-400">
      {{ t('common.noResults') }}
    </div>

    <div v-else class="flex flex-col gap-2">
      <div
        v-for="candidate in candidates"
        :key="candidate.id"
        class="flex items-center justify-between bg-surface-0 p-2 rounded border border-surface-200 text-sm min-w-0"
      >
        <div class="flex flex-wrap gap-x-4 gap-y-1 min-w-0">
          <span>{{ candidate.date }}</span>
          <span class="font-medium">{{ candidate.amount }} {{ candidate.currency?.short_name }}</span>
          <span class="text-surface-500 truncate max-w-xs">{{ candidate.description }}</span>
          <div class="flex items-center gap-2 text-surface-400">
            <AccountDisplay :account="candidate.source" />
            <template v-if="candidate.dest">
              <i class="pi pi-arrow-right text-xs shrink-0"></i>
              <AccountDisplay :account="candidate.dest" />
            </template>
          </div>
        </div>
        <div class="flex gap-2 shrink-0">
          <Button icon="pi pi-clone" severity="warn" size="small" text rounded
            v-tooltip.top="t('review.markDuplicate')" @click="markDuplicate(candidate.id)" />
        </div>
      </div>
    </div>
  </div>
</template>
