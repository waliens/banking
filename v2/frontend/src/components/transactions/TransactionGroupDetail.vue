<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'

const { t } = useI18n()

const props = defineProps({
  group: { type: Object, required: true },
})

const totalPaid = computed(() => Number(props.group.total_paid || 0))
const totalReimbursed = computed(() => Number(props.group.total_reimbursed || 0))
const netExpense = computed(() => Number(props.group.net_expense || 0))
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <h3 class="text-lg font-semibold">
      {{ group.name || `Transaction Group #${group.id}` }}
    </h3>

    <!-- Summary -->
    <div class="grid grid-cols-3 gap-3">
      <div class="bg-red-50 rounded-lg p-3 text-center">
        <div class="text-xs text-surface-500">{{ t('transactions.totalPaid') }}</div>
        <div class="text-sm font-bold text-red-700">
          <CurrencyDisplay :amount="totalPaid" />
        </div>
      </div>
      <div class="bg-green-50 rounded-lg p-3 text-center">
        <div class="text-xs text-surface-500">{{ t('transactions.totalReimbursed') }}</div>
        <div class="text-sm font-bold text-green-700">
          <CurrencyDisplay :amount="totalReimbursed" />
        </div>
      </div>
      <div class="bg-surface-50 rounded-lg p-3 text-center">
        <div class="text-xs text-surface-500">{{ t('flow.netAmount') }}</div>
        <div class="text-sm font-bold">
          <CurrencyDisplay :amount="netExpense" />
        </div>
      </div>
    </div>

    <!-- Member list -->
    <div class="space-y-2">
      <div
        v-for="tx in group.transactions"
        :key="tx.id"
        class="flex items-center gap-3 p-2 bg-surface-0 rounded border border-surface-100 text-sm"
      >
        <span class="text-surface-400 text-xs w-20 shrink-0">{{ tx.date }}</span>
        <span class="truncate flex-1">{{ tx.description }}</span>
        <span class="font-medium whitespace-nowrap">
          <CurrencyDisplay :amount="tx.amount" />
        </span>
        <span v-if="tx.effective_amount != null && String(tx.effective_amount) !== String(tx.amount)" class="text-surface-400 text-xs whitespace-nowrap">
          (<CurrencyDisplay :amount="tx.effective_amount" />)
        </span>
      </div>
    </div>
  </div>
</template>
