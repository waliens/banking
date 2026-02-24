<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import { useActiveWalletStore } from '../stores/activeWallet'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import TransactionFlowTimeline from '../components/flow/TransactionFlowTimeline.vue'
import FlowDetailPanel from '../components/flow/FlowDetailPanel.vue'

const { t } = useI18n()
const walletStore = useWalletStore()
const activeWalletStore = useActiveWalletStore()

const walletId = computed(() => activeWalletStore.activeWalletId)
const wallet = computed(() => activeWalletStore.activeWallet)
const walletAccountIds = computed(() => activeWalletStore.walletAccountIds)

const selectedTx = ref(null)

const drawerVisible = computed({
  get: () => selectedTx.value !== null,
  set: (v) => { if (!v) closeDetail() },
})

function openDetail(txId) {
  selectedTx.value = txId
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

    <div v-else>
      <TransactionFlowTimeline
        v-if="wallet"
        contextType="wallet"
        :contextId="walletId"
        :walletAccountIds="walletAccountIds"
        @select="openDetail"
      />
    </div>

    <Drawer v-model:visible="drawerVisible" position="right" :header="t('flow.transactionDetail')" class="w-full md:w-[28rem]">
      <FlowDetailPanel
        v-if="selectedTx"
        :transactionId="selectedTx"
        @back="closeDetail"
      />
    </Drawer>
  </div>
</template>
