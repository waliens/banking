<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useCategoryStore } from '../../stores/categories'
import CategorySelect from '../common/CategorySelect.vue'
import { useTransactionStore } from '../../stores/transactions'
import { useMLStore } from '../../stores/ml'
import MLSuggestion from '../MLSuggestion.vue'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'
import AccountDisplay from '../common/AccountDisplay.vue'
import CreateTagRuleDialog from './CreateTagRuleDialog.vue'

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

const ruleDialogVisible = ref(false)
const editingEffective = ref(false)
const effectiveAmountInput = ref(null)

function startEditEffective() {
  effectiveAmountInput.value = props.transaction.effective_amount != null
    ? parseFloat(props.transaction.effective_amount)
    : parseFloat(props.transaction.amount)
  editingEffective.value = true
}

async function saveEffectiveAmount() {
  await transactionStore.setEffectiveAmount(props.transaction.id, effectiveAmountInput.value)
  editingEffective.value = false
  emit('categoryChanged')
}

async function clearEffectiveAmount() {
  await transactionStore.setEffectiveAmount(props.transaction.id, null)
  editingEffective.value = false
  emit('categoryChanged')
}

function cancelEditEffective() {
  editingEffective.value = false
}

function onRuleCreated() {
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
      <div v-if="hasEffectiveAmount() && !editingEffective" class="text-sm text-surface-500 mt-1">
        {{ t('transactions.effectiveAmount') }}:
        <CurrencyDisplay
          :amount="transaction.effective_amount"
          :currencySymbol="transaction.currency.symbol || ''"
        />
      </div>
      <!-- Effective amount inline editor -->
      <div v-if="editingEffective" class="mt-2 flex items-center gap-2">
        <InputNumber
          v-model="effectiveAmountInput"
          :min-fraction-digits="2"
          :max-fraction-digits="2"
          class="w-32"
          data-testid="effective-amount-input"
        />
        <Button icon="pi pi-check" severity="success" text size="small" @click="saveEffectiveAmount" data-testid="save-effective" />
        <Button icon="pi pi-times" severity="secondary" text size="small" @click="cancelEditEffective" />
        <Button
          v-if="transaction.effective_amount != null"
          icon="pi pi-trash"
          severity="danger"
          text
          size="small"
          :title="t('transactionDetail.clearOverride')"
          @click="clearEffectiveAmount"
          data-testid="clear-effective"
        />
      </div>
      <div v-if="!editingEffective" class="mt-1">
        <Button
          :label="t('transactionDetail.effectiveAmountOverride')"
          icon="pi pi-pencil"
          severity="secondary"
          text
          size="small"
          @click="startEditEffective"
          data-testid="edit-effective-btn"
        />
      </div>
    </div>

    <!-- Accounts (vertical layout) -->
    <div class="space-y-2">
      <div v-if="transaction.source" class="bg-surface-50 rounded-lg p-3 text-sm">
        <div class="text-xs font-semibold text-surface-500 mb-1">{{ t('transactions.source') }}</div>
        <AccountDisplay :account="transaction.source" />
        <div v-if="transaction.source.institution" class="text-xs text-surface-400">{{ transaction.source.institution }}</div>
      </div>
      <div v-if="transaction.source && transaction.dest" class="flex justify-center">
        <i class="pi pi-arrow-down text-surface-400 text-sm"></i>
      </div>
      <div v-if="transaction.dest" class="bg-surface-50 rounded-lg p-3 text-sm">
        <div class="text-xs font-semibold text-surface-500 mb-1">{{ t('transactions.dest') }}</div>
        <AccountDisplay :account="transaction.dest" />
        <div v-if="transaction.dest.institution" class="text-xs text-surface-400">{{ transaction.dest.institution }}</div>
      </div>
    </div>

    <!-- Category (interactive) -->
    <div class="space-y-2">
      <div class="flex items-center gap-2 text-sm">
        <span class="text-surface-500">{{ t('transactions.category') }}:</span>
      </div>
      <div v-if="transaction.category_splits && transaction.category_splits.length > 1" class="flex items-center gap-2 text-sm text-surface-600">
        <i class="pi pi-tags"></i>
        <span>{{ t('transactionDetail.multiCategory', { count: transaction.category_splits.length }) }}</span>
      </div>
      <CategorySelect
        v-else
        :modelValue="transaction.category_splits && transaction.category_splits.length === 1 ? transaction.category_splits[0].id_category : null"
        @update:modelValue="onCategoryChange"
        :placeholder="t('transactions.uncategorized')"
        :showClear="true"
        class="w-full"
      />
      <MLSuggestion
        v-if="mlStore.predictions[transaction.id]"
        :categoryName="mlStore.predictions[transaction.id].category_name"
        :categoryColor="mlStore.predictions[transaction.id].category_color"
        :probability="mlStore.predictions[transaction.id].probability"
        @accept="acceptSuggestion(mlStore.predictions[transaction.id].category_id)"
      />
      <Button
        :label="t('rules.createFromTransaction')"
        icon="pi pi-bolt"
        severity="secondary"
        text
        size="small"
        class="mt-1"
        @click="ruleDialogVisible = true"
      />
      <CreateTagRuleDialog
        v-model:visible="ruleDialogVisible"
        :transaction="transaction"
        @created="onRuleCreated"
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
      <div v-if="transaction.id_import">
        <router-link :to="`/imports/${transaction.id_import}`" class="text-primary-500 hover:underline">
          {{ t('import.viewDetails') }}
        </router-link>
      </div>
      <div v-if="transaction.raw_metadata" class="mt-2">
        <details class="cursor-pointer">
          <summary class="text-surface-500">Raw metadata</summary>
          <pre class="text-xs bg-surface-50 rounded p-2 mt-1 overflow-x-auto">{{ JSON.stringify(transaction.raw_metadata, null, 2) }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>
