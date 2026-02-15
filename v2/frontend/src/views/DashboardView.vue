<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccountStore } from '../stores/accounts'
import { useTransactionStore } from '../stores/transactions'

const { t } = useI18n()
const accountStore = useAccountStore()
const transactionStore = useTransactionStore()

onMounted(async () => {
  await Promise.all([
    accountStore.fetchAccounts(),
    transactionStore.fetchTransactions({ count: 10 }),
  ])
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">{{ t('nav.dashboard') }}</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-surface-0 rounded-xl shadow p-4">
        <h2 class="text-sm text-surface-500 mb-1">{{ t('accounts.title') }}</h2>
        <p class="text-2xl font-bold">{{ accountStore.accounts.length }}</p>
      </div>
      <div class="bg-surface-0 rounded-xl shadow p-4">
        <h2 class="text-sm text-surface-500 mb-1">{{ t('transactions.title') }}</h2>
        <p class="text-2xl font-bold">{{ transactionStore.totalCount }}</p>
      </div>
    </div>

    <div class="bg-surface-0 rounded-xl shadow p-4">
      <h2 class="text-lg font-semibold mb-4">{{ t('transactions.title') }}</h2>
      <div v-if="transactionStore.loading" class="text-center py-8 text-surface-400">
        {{ t('common.loading') }}
      </div>
      <div v-else-if="transactionStore.transactions.length === 0" class="text-center py-8 text-surface-400">
        {{ t('common.noResults') }}
      </div>
      <div v-else class="flex flex-col divide-y divide-surface-100">
        <div
          v-for="t in transactionStore.transactions"
          :key="t.id"
          class="flex items-center justify-between py-3 px-2"
        >
          <div class="flex-1 min-w-0">
            <p class="truncate font-medium">{{ t.description || '—' }}</p>
            <p class="text-sm text-surface-400">{{ t.date }}</p>
          </div>
          <div class="text-right ml-4">
            <p class="font-semibold" :class="t.id_source ? 'text-red-500' : 'text-green-600'">
              {{ t.id_source ? '-' : '+' }}{{ t.amount }} {{ t.currency?.symbol }}
            </p>
            <p class="text-xs text-surface-400">{{ t.category?.name || '' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
