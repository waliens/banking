<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import api from '../../services/api'
import { useTransactionFlowStore } from '../../stores/transactionFlow'
import { useActiveWalletStore } from '../../stores/activeWallet'
import { useTransactionGroupStore } from '../../stores/transactionGroups'
import TransactionDetail from '../transactions/TransactionDetail.vue'
import TransactionGroupDetail from '../transactions/TransactionGroupDetail.vue'

const { t } = useI18n()
const flowStore = useTransactionFlowStore()
const activeWalletStore = useActiveWalletStore()
const groupStore = useTransactionGroupStore()

const props = defineProps({
  transactionId: { type: Number, required: true },
})

const emit = defineEmits(['back'])

const transaction = ref(null)
const group = ref(null)
const loading = ref(false)

async function loadDetail() {
  loading.value = true
  transaction.value = null
  group.value = null

  try {
    const { data } = await api.get(`/transactions/${props.transactionId}`)
    transaction.value = data

    if (data.id_transaction_group && activeWalletStore.activeWalletId) {
      const cached = flowStore.groupCache[data.id_transaction_group]
      if (cached) {
        group.value = cached
      } else {
        group.value = await groupStore.fetchGroup(data.id_transaction_group, activeWalletStore.activeWalletId)
      }
    }
  } finally {
    loading.value = false
  }
}

function onCategoryChanged() {
  loadDetail()
}

watch(() => props.transactionId, loadDetail, { immediate: true })
</script>

<template>
  <div class="p-4">
    <div class="flex items-center gap-2 mb-4">
      <Button
        :label="t('flow.backToFlow')"
        icon="pi pi-arrow-left"
        text
        size="small"
        @click="emit('back')"
      />
      <router-link v-if="transaction" :to="`/transactions/${transaction.id}`">
        <Button :label="t('transactionDetail.openFullPage')" icon="pi pi-external-link" severity="secondary" size="small" text />
      </router-link>
    </div>

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
