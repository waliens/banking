<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import { useCategoryStore } from '../../stores/categories'
import { useTransactionStore } from '../../stores/transactions'
import { useMLStore } from '../../stores/ml'
import MLSuggestion from '../MLSuggestion.vue'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'

const { t } = useI18n()
const categoryStore = useCategoryStore()
const transactionStore = useTransactionStore()
const mlStore = useMLStore()

const props = defineProps({
  transaction: { type: Object, required: true },
})

const emit = defineEmits(['categoryChanged'])

function hasEffectiveAmount() {
  const tx = props.transaction
  return tx.effective_amount != null && String(tx.effective_amount) !== String(tx.amount)
}

async function onCategoryChange(categoryId) {
  await transactionStore.setCategory(props.transaction.id, categoryId)
  emit('categoryChanged')
}

async function acceptSuggestion(categoryId) {
  await transactionStore.setCategory(props.transaction.id, categoryId)
  emit('categoryChanged')
}

onMounted(async () => {
  if (!categoryStore.categories.length) {
    await categoryStore.fetchCategories()
  }
  // Try to get ML prediction (optional, fail silently)
  try {
    await mlStore.predictTransactions([props.transaction.id])
  } catch {
    // ML predictions are optional
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div>
      <h3 class="text-lg font-semibold">{{ transaction.description }}</h3>
      <div class="flex items-center gap-2 mt-1">
        <span class="text-sm text-surface-500">{{ transaction.date }}</span>
        <Tag
          v-if="transaction.is_reviewed"
          :value="t('flow.reviewed')"
          severity="success"
          class="text-xs"
        />
        <Tag
          v-else
          :value="t('flow.notReviewed')"
          severity="warn"
          class="text-xs"
        />
      </div>
    </div>

    <!-- Amount -->
    <div class="bg-surface-50 rounded-lg p-3">
      <div class="text-2xl font-bold">
        <CurrencyDisplay
          :amount="transaction.amount"
          :currencySymbol="transaction.currency_symbol || ''"
        />
      </div>
      <div v-if="hasEffectiveAmount()" class="text-sm text-surface-500 mt-1">
        {{ t('transactions.effectiveAmount') }}:
        <CurrencyDisplay
          :amount="transaction.effective_amount"
          :currencySymbol="transaction.currency_symbol || ''"
        />
      </div>
    </div>

    <!-- Accounts -->
    <div class="flex items-center gap-2 text-sm">
      <span class="text-surface-500">{{ t('transactions.source') }}:</span>
      <span class="font-medium">{{ transaction.source_name || `#${transaction.id_source}` }}</span>
      <i class="pi pi-arrow-right text-surface-400 text-xs"></i>
      <span class="text-surface-500">{{ t('transactions.dest') }}:</span>
      <span class="font-medium">{{ transaction.dest_name || `#${transaction.id_dest}` }}</span>
    </div>

    <!-- Category (interactive) -->
    <div class="space-y-2">
      <div class="flex items-center gap-2 text-sm">
        <span class="text-surface-500">{{ t('transactions.category') }}:</span>
      </div>
      <Select
        :modelValue="transaction.id_category"
        @update:modelValue="onCategoryChange"
        :options="categoryStore.categories"
        optionLabel="name"
        optionValue="id"
        :placeholder="t('transactions.uncategorized')"
        class="w-full"
      />
      <MLSuggestion
        v-if="mlStore.predictions[transaction.id]"
        :categoryName="mlStore.predictions[transaction.id].category_name"
        :categoryColor="mlStore.predictions[transaction.id].category_color"
        :probability="mlStore.predictions[transaction.id].probability"
        @accept="acceptSuggestion(mlStore.predictions[transaction.id].category_id)"
      />
    </div>

    <!-- Notes -->
    <div v-if="transaction.notes" class="text-sm">
      <span class="text-surface-500">Notes:</span>
      <p class="mt-1">{{ transaction.notes }}</p>
    </div>

    <!-- Metadata -->
    <div class="text-xs text-surface-400 space-y-1 pt-2 border-t border-surface-100">
      <div v-if="transaction.data_source">Source: {{ transaction.data_source }}</div>
      <div v-if="transaction.external_id">ID: {{ transaction.external_id }}</div>
    </div>
  </div>
</template>
