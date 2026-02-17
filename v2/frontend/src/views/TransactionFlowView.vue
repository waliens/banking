<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import Button from 'primevue/button'
import TransactionFlowTimeline from '../components/flow/TransactionFlowTimeline.vue'
import FlowDetailPanel from '../components/flow/FlowDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const walletStore = useWalletStore()

const walletId = computed(() => Number(route.params.id))
const wallet = computed(() => walletStore.wallets.find((w) => w.id === walletId.value))
const walletAccountIds = computed(() =>
  (wallet.value?.accounts || []).map((a) => a.id_account ?? a.id),
)

const selectedTx = computed(() => {
  const tx = route.query.tx
  return tx ? Number(tx) : null
})

function openDetail(txId) {
  router.push({ query: { ...route.query, tx: txId } })
}

function closeDetail() {
  const query = { ...route.query }
  delete query.tx
  router.push({ query })
}

onMounted(async () => {
  if (!walletStore.wallets.length) {
    await walletStore.fetchWallets()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <Button icon="pi pi-arrow-left" text rounded @click="router.push(`/wallets/${walletId}`)" />
      <div>
        <h1 class="text-2xl font-bold">{{ t('flow.title') }}</h1>
        <p v-if="wallet" class="text-sm text-surface-500">{{ wallet.name }}</p>
      </div>
    </div>

    <div class="relative overflow-hidden">
      <div
        :class="selectedTx ? '-translate-x-full' : ''"
        class="transition-transform duration-300"
      >
        <TransactionFlowTimeline
          v-if="wallet"
          contextType="wallet"
          :contextId="walletId"
          :walletAccountIds="walletAccountIds"
          @select="openDetail"
        />
      </div>
      <div
        :class="selectedTx ? 'translate-x-0' : 'translate-x-full'"
        class="absolute inset-0 transition-transform duration-300 bg-surface-50"
      >
        <FlowDetailPanel
          v-if="selectedTx"
          :transactionId="selectedTx"
          @back="closeDetail"
        />
      </div>
    </div>
  </div>
</template>
