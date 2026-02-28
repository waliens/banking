<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import SelectButton from 'primevue/selectbutton'
import { useTransactionStore } from '../stores/transactions'
import { useTransactionGroupStore } from '../stores/transactionGroups'
import { useCategoryStore } from '../stores/categories'
import { useActiveWalletStore } from '../stores/activeWallet'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import TransactionGroupDetail from '../components/transactions/TransactionGroupDetail.vue'
import TransactionGroupDialog from '../components/transactions/TransactionGroupDialog.vue'
import DuplicateCandidates from '../components/transactions/DuplicateCandidates.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'
import CategorySelect from '../components/common/CategorySelect.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const transactionStore = useTransactionStore()
const groupStore = useTransactionGroupStore()
const categoryStore = useCategoryStore()
const activeWalletStore = useActiveWalletStore()

const transaction = ref(null)
const originalTransaction = ref(null)
const group = ref(null)
const loading = ref(false)

async function loadTransaction() {
  loading.value = true
  transaction.value = null
  originalTransaction.value = null
  group.value = null

  try {
    const id = Number(route.params.id)
    transaction.value = await transactionStore.fetchTransaction(id)

    const promises = [categoryStore.fetchCategories()]

    if (transaction.value.id_duplicate_of) {
      promises.push(
        transactionStore.fetchTransaction(transaction.value.id_duplicate_of)
          .then((data) => { originalTransaction.value = data })
      )
    }

    if (transaction.value.id_transaction_group && activeWalletStore.activeWalletId) {
      promises.push(
        groupStore.fetchGroup(transaction.value.id_transaction_group, activeWalletStore.activeWalletId)
          .then((data) => { group.value = data })
      )
    }

    await Promise.all(promises)
  } finally {
    loading.value = false
  }
}

const groupDialogVisible = ref(false)

function openGroupDialog() {
  groupDialogVisible.value = true
}

function onGroupSaved() {
  loadTransaction()
}

function onGroupDeleted() {
  loadTransaction()
}

async function removeFromGroup() {
  if (!group.value) return
  const remainingIds = group.value.transactions
    .filter((t) => t.id !== transaction.value.id)
    .map((t) => t.id)
  if (remainingIds.length === 0) {
    await groupStore.deleteGroup(group.value.id)
  } else {
    await groupStore.updateGroup(group.value.id, {
      name: group.value.name,
      transaction_ids: remainingIds,
      wallet_id: activeWalletStore.activeWalletId,
    })
  }
  await loadTransaction()
}

async function unmarkDuplicate() {
  await transactionStore.unmarkDuplicate(transaction.value.id)
  await loadTransaction()
}

function onCategoryChanged() {
  loadTransaction()
}

function onDuplicateResolved() {
  loadTransaction()
}

// --- Category Splits ---
const splitEditing = ref(false)
const splitRows = ref([])
const splitMode = ref('amount')
const splitModeOptions = computed(() => [
  { label: t('transactionDetail.modeAmount'), value: 'amount' },
  { label: t('transactionDetail.modeRatio'), value: 'ratio' },
  { label: t('transactionDetail.modeParts'), value: 'parts' },
])

const splitTarget = computed(() => {
  if (!transaction.value) return { splits: [], total: 0, isGroup: false, targetId: null }
  const tx = transaction.value
  if (group.value) {
    return {
      splits: group.value.category_splits || [],
      total: parseFloat(group.value.net_expense || 0),
      isGroup: true,
      targetId: group.value.id,
    }
  }
  const eff = tx.effective_amount != null ? parseFloat(tx.effective_amount) : parseFloat(tx.amount)
  return {
    splits: tx.category_splits || [],
    total: Math.abs(eff),
    isGroup: false,
    targetId: tx.id,
  }
})

const splitAllocated = computed(() => splitRows.value.reduce((sum, r) => sum + (r.amount || 0), 0))
const splitRemaining = computed(() => splitTarget.value.total - splitAllocated.value)
const splitValid = computed(() => {
  return splitRows.value.length >= 2
    && splitRows.value.every((r) => r.id_category != null && r.amount > 0)
    && Math.abs(splitRemaining.value) < 0.01
})

// Display values for ratio/parts modes (indexes match splitRows)
const splitDisplayValues = ref([])

function syncDisplayFromAmounts() {
  const total = splitTarget.value.total
  if (splitMode.value === 'ratio') {
    splitDisplayValues.value = splitRows.value.map((r) =>
      total > 0 ? Math.round(((r.amount || 0) / total) * 100) : 0
    )
  } else if (splitMode.value === 'parts') {
    // Find GCD-like integer parts — default to 1 per row
    splitDisplayValues.value = splitRows.value.map(() => 1)
  }
}

function onDisplayValueChange(idx, val) {
  const total = splitTarget.value.total
  if (splitMode.value === 'ratio') {
    splitDisplayValues.value[idx] = val
    // Convert percentage to amount
    splitRows.value[idx].amount = Math.round(((val || 0) / 100) * total * 100) / 100
  } else if (splitMode.value === 'parts') {
    splitDisplayValues.value[idx] = val
    // Convert parts to amounts proportionally
    const totalParts = splitDisplayValues.value.reduce((s, p) => s + (p || 0), 0)
    if (totalParts > 0) {
      let allocated = 0
      splitRows.value.forEach((row, i) => {
        if (i === splitRows.value.length - 1) {
          // Last row gets the remainder to avoid rounding errors
          row.amount = Math.round((total - allocated) * 100) / 100
        } else {
          row.amount = Math.round(((splitDisplayValues.value[i] || 0) / totalParts) * total * 100) / 100
          allocated += row.amount
        }
      })
    }
  }
}

function onModeChange(newMode) {
  splitMode.value = newMode
  syncDisplayFromAmounts()
}

function startSplitEdit() {
  const { splits, total } = splitTarget.value
  if (splits.length >= 2) {
    splitRows.value = splits.map((s) => ({ id_category: s.id_category, amount: parseFloat(s.amount) }))
  } else if (splits.length === 1) {
    splitRows.value = [
      { id_category: splits[0].id_category, amount: parseFloat(splits[0].amount) },
      { id_category: null, amount: 0 },
    ]
  } else {
    splitRows.value = [
      { id_category: null, amount: 0 },
      { id_category: null, amount: 0 },
    ]
  }
  splitMode.value = 'amount'
  syncDisplayFromAmounts()
  splitEditing.value = true
}

function addSplitRow() {
  splitRows.value.push({ id_category: null, amount: 0 })
  splitDisplayValues.value.push(splitMode.value === 'parts' ? 1 : 0)
}

function removeSplitRow(idx) {
  splitRows.value.splice(idx, 1)
  splitDisplayValues.value.splice(idx, 1)
  if (splitMode.value === 'parts') {
    // Recalculate amounts from remaining parts
    onDisplayValueChange(0, splitDisplayValues.value[0])
  }
}

function cancelSplitEdit() {
  splitEditing.value = false
}

async function saveSplits() {
  if (!splitValid.value) return
  const splits = splitRows.value.map((r) => ({ id_category: r.id_category, amount: r.amount }))
  const { isGroup, targetId } = splitTarget.value
  if (isGroup) {
    await groupStore.setGroupCategorySplits(targetId, splits, activeWalletStore.activeWalletId)
  } else {
    await transactionStore.setCategorySplits(targetId, splits)
  }
  splitEditing.value = false
  await loadTransaction()
}

async function clearSplits() {
  const { isGroup, targetId } = splitTarget.value
  if (isGroup) {
    await groupStore.clearGroupCategorySplits(targetId, activeWalletStore.activeWalletId)
  } else {
    await transactionStore.clearCategorySplits(targetId)
  }
  splitEditing.value = false
  await loadTransaction()
}

function getCategoryName(id) {
  if (!id) return ''
  const cat = categoryStore.categoryMap.get(id)
  return cat ? cat.name : `#${id}`
}

function getCategoryColor(id) {
  if (!id) return '#ccc'
  const cat = categoryStore.categoryMap.get(id)
  return cat ? cat.color : '#ccc'
}

watch(() => route.params.id, loadTransaction, { immediate: true })
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <Button
      :label="t('flow.backToFlow')"
      icon="pi pi-arrow-left"
      text
      size="small"
      class="mb-4"
      @click="router.back()"
    />

    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
    </div>

    <template v-else-if="transaction">
      <!-- Transaction Detail -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <TransactionDetail :transaction="transaction" @categoryChanged="onCategoryChanged" />
      </div>

      <!-- Duplicate-of status -->
      <div v-if="transaction.id_duplicate_of" class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
        <h3 class="text-sm font-semibold text-amber-800 mb-2">{{ t('transactionDetail.duplicateOf') }}</h3>
        <div v-if="originalTransaction" class="flex items-center gap-4 text-sm mb-3">
          <span>{{ originalTransaction.date }}</span>
          <span class="font-medium">
            <CurrencyDisplay :amount="originalTransaction.amount" :currencySymbol="originalTransaction.currency?.symbol || ''" />
          </span>
          <span class="text-surface-500 truncate">{{ originalTransaction.description }}</span>
          <AccountDisplay v-if="originalTransaction.source" :account="originalTransaction.source" />
        </div>
        <div class="flex gap-2">
          <router-link :to="`/transactions/${transaction.id_duplicate_of}`">
            <Button :label="t('transactionDetail.viewOriginal')" severity="secondary" size="small" icon="pi pi-external-link" />
          </router-link>
          <Button :label="t('transactionDetail.unmarkDuplicate')" severity="warn" size="small" @click="unmarkDuplicate" />
        </div>
      </div>

      <!-- Duplicate Candidates -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.duplicateCandidates') }}</h3>
        <DuplicateCandidates :transactionId="transaction.id" @resolved="onDuplicateResolved" />
      </div>

      <!-- Transaction Group -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.transactionGroup') }}</h3>
        <template v-if="group">
          <TransactionGroupDetail :group="group" />
          <div class="flex gap-2 mt-3">
            <Button
              :label="t('transactionDetail.editGroup')"
              icon="pi pi-pencil"
              severity="secondary"
              size="small"
              @click="openGroupDialog"
              data-testid="edit-group-btn"
            />
            <Button
              :label="t('transactionDetail.removeFromGroup')"
              icon="pi pi-times"
              severity="warn"
              size="small"
              @click="removeFromGroup"
              data-testid="remove-from-group-btn"
            />
          </div>
        </template>
        <template v-else>
          <div class="flex items-center gap-2">
            <Button
              :label="t('transactionDetail.linkTransactions')"
              icon="pi pi-link"
              severity="secondary"
              size="small"
              :disabled="!activeWalletStore.activeWalletId"
              @click="openGroupDialog"
              data-testid="link-transactions-btn"
            />
            <span v-if="!activeWalletStore.activeWalletId" class="text-xs text-surface-400">
              {{ t('transactionDetail.noWalletForGroup') }}
            </span>
          </div>
        </template>
      </div>

      <!-- Category Splits -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4 overflow-hidden">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.categorySplits') }}</h3>

        <template v-if="!splitEditing">
          <!-- Display existing splits -->
          <div v-if="splitTarget.splits.length >= 2" class="space-y-2 mb-3">
            <div
              v-for="(split, idx) in splitTarget.splits"
              :key="idx"
              class="flex items-center gap-2 text-sm"
            >
              <span
                class="w-3 h-3 rounded-full shrink-0"
                :style="{ backgroundColor: getCategoryColor(split.id_category) }"
              ></span>
              <span class="flex-1">{{ getCategoryName(split.id_category) }}</span>
              <span class="font-medium">{{ parseFloat(split.amount).toFixed(2) }}</span>
            </div>
          </div>
          <div v-else-if="splitTarget.splits.length === 1" class="text-sm text-surface-500 mb-3">
            {{ getCategoryName(splitTarget.splits[0].id_category) }} — {{ parseFloat(splitTarget.splits[0].amount).toFixed(2) }}
          </div>

          <div class="flex gap-2">
            <Button
              v-if="splitTarget.splits.length >= 2"
              :label="t('transactionDetail.editSplits')"
              icon="pi pi-pencil"
              severity="secondary"
              size="small"
              @click="startSplitEdit"
            />
            <Button
              v-if="splitTarget.splits.length >= 2"
              :label="t('transactionDetail.resetToSingle')"
              icon="pi pi-times"
              severity="warn"
              size="small"
              text
              @click="clearSplits"
            />
            <Button
              v-if="splitTarget.splits.length < 2"
              :label="t('transactionDetail.splitCategories')"
              icon="pi pi-tags"
              severity="secondary"
              size="small"
              @click="startSplitEdit"
            />
          </div>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <!-- Mode toggle -->
          <div class="mb-3">
            <SelectButton
              :modelValue="splitMode"
              @update:modelValue="onModeChange"
              :options="splitModeOptions"
              optionLabel="label"
              optionValue="value"
              :allowEmpty="false"
              class="text-xs"
            />
          </div>

          <div class="space-y-2 mb-3">
            <div v-for="(row, idx) in splitRows" :key="idx" class="flex items-center gap-2 min-w-0">
              <CategorySelect
                v-model="row.id_category"
                :placeholder="t('categories.selectCategory')"
                class="flex-1 min-w-0"
              />
              <!-- Amount mode: edit absolute amounts -->
              <InputNumber
                v-if="splitMode === 'amount'"
                v-model="row.amount"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
                inputClass="w-full"
                class="w-24 shrink-0"
              />
              <!-- Ratio mode: edit percentages -->
              <InputNumber
                v-else-if="splitMode === 'ratio'"
                :modelValue="splitDisplayValues[idx]"
                @update:modelValue="(v) => onDisplayValueChange(idx, v)"
                suffix="%"
                :min="0"
                :max="100"
                inputClass="w-full"
                class="w-24 shrink-0"
              />
              <!-- Parts mode: edit integer parts -->
              <InputNumber
                v-else
                :modelValue="splitDisplayValues[idx]"
                @update:modelValue="(v) => onDisplayValueChange(idx, v)"
                :min="1"
                :showButtons="true"
                inputClass="w-full"
                class="w-24 shrink-0"
              />
              <Button
                icon="pi pi-times"
                severity="danger"
                text
                size="small"
                class="shrink-0"
                @click="removeSplitRow(idx)"
                :disabled="splitRows.length <= 2"
              />
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm mb-3">
            <span>{{ t('transactionDetail.splitTotal') }}: {{ splitAllocated.toFixed(2) }} / {{ splitTarget.total.toFixed(2) }}</span>
            <span v-if="Math.abs(splitRemaining) > 0.01" class="text-red-500">
              {{ t('transactionDetail.splitRemaining') }}: {{ splitRemaining.toFixed(2) }}
            </span>
          </div>

          <div class="flex flex-wrap gap-2">
            <Button
              :label="t('transactionDetail.addSplit')"
              icon="pi pi-plus"
              severity="secondary"
              size="small"
              text
              @click="addSplitRow"
            />
            <span class="flex-1" />
            <Button
              :label="t('common.cancel')"
              severity="secondary"
              size="small"
              text
              @click="cancelSplitEdit"
            />
            <Button
              :label="t('common.save')"
              icon="pi pi-check"
              size="small"
              :disabled="!splitValid"
              @click="saveSplits"
            />
          </div>
        </template>
      </div>

      <!-- Group Dialog -->
      <TransactionGroupDialog
        :visible="groupDialogVisible"
        @update:visible="groupDialogVisible = $event"
        :group="group"
        :initialTransaction="!group ? transaction : null"
        :walletId="activeWalletStore.activeWalletId"
        :walletAccountIds="activeWalletStore.walletAccountIds"
        @saved="onGroupSaved"
        @deleted="onGroupDeleted"
      />
    </template>
  </div>
</template>
