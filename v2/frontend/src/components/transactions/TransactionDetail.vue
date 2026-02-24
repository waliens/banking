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
import AccountDisplay from '../common/AccountDisplay.vue'

const { t } = useI18n()
const categoryStore = useCategoryStore()
const transactionStore = useTransactionStore()
const mlStore = useMLStore()

const props = defineProps({
  transaction: { type: Object, required: true },
  showFullDetails: { type: Boolean, default: false },
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
        <Tag
          v-if="transaction.id_duplicate_of"
          value="Duplicate"
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
          :currencySymbol="transaction.currency.symbol || ''"
        />
      </div>
      <div v-if="hasEffectiveAmount()" class="text-sm text-surface-500 mt-1">
        {{ t('transactions.effectiveAmount') }}:
        <CurrencyDisplay
          :amount="transaction.effective_amount"
          :currencySymbol="transaction.currency.symbol || ''"
        />
      </div>
    </div>

    <!-- Accounts (enhanced for showFullDetails) -->
    <div v-if="showFullDetails" class="space-y-3">
      <div v-if="transaction.source" class="bg-surface-50 rounded-lg p-3 text-sm">
        <div class="text-xs font-semibold text-surface-500 mb-1">{{ t('transactions.source') }}</div>
        <AccountDisplay :account="transaction.source" />
        <div v-if="transaction.source.institution" class="text-xs text-surface-400">{{ transaction.source.institution }}</div>
      </div>
      <div v-if="transaction.dest" class="bg-surface-50 rounded-lg p-3 text-sm">
        <div class="text-xs font-semibold text-surface-500 mb-1">{{ t('transactions.dest') }}</div>
        <AccountDisplay :account="transaction.dest" />
        <div v-if="transaction.dest.institution" class="text-xs text-surface-400">{{ transaction.dest.institution }}</div>
      </div>
    </div>
    <div v-else class="flex items-start gap-3 text-sm">
      <div>
        <div class="text-xs text-surface-500 mb-1">{{ t('transactions.source') }}</div>
        <AccountDisplay :account="transaction.source || (transaction.id_source ? { name: null, number: `#${transaction.id_source}` } : null)" />
      </div>
      <i class="pi pi-arrow-right text-surface-400 text-xs mt-1"></i>
      <div>
        <div class="text-xs text-surface-500 mb-1">{{ t('transactions.dest') }}</div>
        <AccountDisplay :account="transaction.dest || (transaction.id_dest ? { name: null, number: `#${transaction.id_dest}` } : null)" />
      </div>
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
      >
        <template #option="{ option }">
          <div class="flex items-center gap-2">
            <i v-if="option.icon" :class="option.icon" class="text-sm"></i>
            <span>{{ option.name }}</span>
          </div>
        </template>
      </Select>
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
      <div v-if="showFullDetails && transaction.id_import">
        <router-link :to="`/imports/${transaction.id_import}`" class="text-primary-500 hover:underline">
          {{ t('import.viewDetails') }}
        </router-link>
      </div>
      <div v-if="showFullDetails && transaction.raw_metadata" class="mt-2">
        <details class="cursor-pointer">
          <summary class="text-surface-500">Raw metadata</summary>
          <pre class="text-xs bg-surface-50 rounded p-2 mt-1 overflow-x-auto">{{ JSON.stringify(transaction.raw_metadata, null, 2) }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>
