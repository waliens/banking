<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import { useActiveWalletStore } from '../stores/activeWallet'
import Button from 'primevue/button'
import TransactionFlowTimeline from '../components/flow/TransactionFlowTimeline.vue'
import FlowDetailPanel from '../components/flow/FlowDetailPanel.vue'

const { t } = useI18n()
const walletStore = useWalletStore()
const activeWalletStore = useActiveWalletStore()

const walletId = computed(() => activeWalletStore.activeWalletId)
const wallet = computed(() => activeWalletStore.activeWallet)
const walletAccountIds = computed(() => activeWalletStore.walletAccountIds)

const selectedTx = ref(null)
const detailContainerRef = ref(null)

function openDetail(txId) {
  selectedTx.value = txId
  nextTick(() => {
    if (detailContainerRef.value) {
      detailContainerRef.value.scrollTop = 0
    }
  })
}

function closeDetail() {
  selectedTx.value = null
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
      <div>
        <h1 class="text-2xl font-bold">{{ t('flow.title') }}</h1>
        <p v-if="wallet" class="text-sm text-surface-500">{{ wallet.name }}</p>
      </div>
    </div>

    <!-- Empty state if no wallet -->
    <div v-if="!walletId" class="text-center py-16 text-surface-400">
      <i class="pi pi-briefcase text-5xl mb-4 block" />
      <p>{{ t('wallet.noWalletSelected') }}</p>
      <router-link to="/" class="text-primary-500 mt-2 inline-block">
        {{ t('wallet.selectWallet') }}
      </router-link>
    </div>

    <div v-else class="relative overflow-hidden">
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
        ref="detailContainerRef"
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
