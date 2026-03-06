<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useWalletStore } from '../stores/wallets'
import { useActiveWalletStore } from '../stores/activeWallet'
import Button from 'primevue/button'
import TransactionFlowTimeline from '../components/flow/TransactionFlowTimeline.vue'

defineOptions({ name: 'TransactionFlowView' })

const { t } = useI18n()
const router = useRouter()
const walletStore = useWalletStore()
const activeWalletStore = useActiveWalletStore()

const walletId = computed(() => activeWalletStore.activeWalletId)
const wallet = computed(() => activeWalletStore.activeWallet)
const walletAccountIds = computed(() => activeWalletStore.walletAccountIds)

function openDetail(txId) {
  router.push(`/transactions/${txId}`)
}

function openGroupDetail(groupId) {
  router.push(`/groups/${groupId}`)
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
        @select-group="openGroupDetail"
      />
    </div>

  </div>
</template>
