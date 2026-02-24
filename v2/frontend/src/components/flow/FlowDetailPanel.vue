<script setup>
import { ref, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import api from '../../services/api'
import { useTransactionFlowStore } from '../../stores/transactionFlow'
import TransactionDetail from '../transactions/TransactionDetail.vue'
import TransactionGroupDetail from '../transactions/TransactionGroupDetail.vue'

const { t } = useI18n()
const flowStore = useTransactionFlowStore()

const props = defineProps({
  transactionId: { type: Number, required: true },
})

const emit = defineEmits(['back'])

const transaction = ref(null)
const group = ref(null)
const loading = ref(false)
const containerRef = ref(null)

async function loadDetail() {
  loading.value = true
  transaction.value = null
  group.value = null

  try {
    const { data } = await api.get(`/transactions/${props.transactionId}`)
    transaction.value = data

    if (data.id_transaction_group) {
      const cached = flowStore.groupCache[data.id_transaction_group]
      if (cached) {
        group.value = cached
      } else {
        const groupRes = await api.get(`/transaction-groups/${data.id_transaction_group}`)
        group.value = groupRes.data
      }
    }
  } finally {
    loading.value = false
    await nextTick()
    if (containerRef.value) {
      containerRef.value.scrollTop = 0
    }
  }
}

function onCategoryChanged() {
  loadDetail()
}

watch(() => props.transactionId, loadDetail, { immediate: true })
</script>

<template>
  <div ref="containerRef" class="p-4 overflow-y-auto h-full">
    <Button
      :label="t('flow.backToFlow')"
      icon="pi pi-arrow-left"
      text
      size="small"
      class="mb-4"
      @click="emit('back')"
    />

    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
    </div>

    <template v-else-if="transaction">
      <TransactionDetail :transaction="transaction" @categoryChanged="onCategoryChanged" />

      <div v-if="group" class="mt-6 pt-4 border-t border-surface-200">
        <TransactionGroupDetail :group="group" />
      </div>
    </template>
  </div>
</template>
