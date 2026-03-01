<script setup>
import { useI18n } from 'vue-i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'
import AccountDisplay from '../common/AccountDisplay.vue'

defineProps({
  transactions: { type: Array, required: true },
  emptyMessage: { type: String, default: null },
})

const emit = defineEmits(['select'])

const { t } = useI18n()
</script>

<template>
  <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
    <DataTable
      :value="transactions"
      stripedRows
      class="text-sm"
      @row-click="({ data }) => emit('select', data.id)"
      selectionMode="single"
      :rowClass="() => 'cursor-pointer'"
    >
      <Column field="date" :header="t('transactions.date')" style="width: 110px" />
      <Column field="description" :header="t('transactions.description')" />
      <Column :header="t('transactions.source')" style="width: 150px">
        <template #body="{ data }">
          <AccountDisplay :account="data.source" />
        </template>
      </Column>
      <Column :header="t('transactions.amount')" style="width: 120px">
        <template #body="{ data }">
          <CurrencyDisplay
            :amount="data.amount"
            :currencySymbol="data.currency?.symbol || ''"
            :showSign="true"
            colored
            class="font-medium"
          />
        </template>
      </Column>
      <slot />
    </DataTable>
    <p v-if="emptyMessage && !transactions.length" class="text-surface-500 text-center py-8">{{ emptyMessage }}</p>
  </div>
</template>
