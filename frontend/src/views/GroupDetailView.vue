<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import SelectButton from 'primevue/selectbutton'
import { useTransactionGroupStore } from '../stores/transactionGroups'
import { useCategoryStore } from '../stores/categories'
import { useActiveWalletStore } from '../stores/activeWallet'
import TransactionGroupDetail from '../components/transactions/TransactionGroupDetail.vue'
import TransactionGroupDialog from '../components/transactions/TransactionGroupDialog.vue'
import CategorySelect from '../components/common/CategorySelect.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const groupStore = useTransactionGroupStore()
const categoryStore = useCategoryStore()
const activeWalletStore = useActiveWalletStore()

const group = ref(null)
const loading = ref(false)

async function loadGroup() {
  loading.value = true
  group.value = null

  try {
    const id = Number(route.params.id)
    const walletId = activeWalletStore.activeWalletId
    const [data] = await Promise.all([
      groupStore.fetchGroup(id, walletId),
      categoryStore.fetchCategories(),
    ])
    group.value = data
  } finally {
    loading.value = false
  }
}

const groupDialogVisible = ref(false)

function openGroupDialog() {
  groupDialogVisible.value = true
}

function onGroupSaved() {
  loadGroup()
}

function onGroupDeleted() {
  router.back()
}

async function deleteGroup() {
  if (!group.value) return
  await groupStore.deleteGroup(group.value.id)
  router.back()
}

function openTransaction(txId) {
  router.push(`/transactions/${txId}`)
}

// --- Single category assignment ---
const currentCategoryId = computed(() => {
  if (!group.value) return null
  const splits = group.value.category_splits || []
  return splits.length === 1 ? splits[0].id_category : null
})

const isMultiCategory = computed(() => {
  const splits = group.value?.category_splits || []
  return splits.length > 1
})

async function onCategoryChanged(categoryId) {
  if (!group.value) return
  const walletId = activeWalletStore.activeWalletId
  if (!walletId) return
  if (categoryId) {
    await groupStore.setGroupCategorySplits(group.value.id, [{ id_category: categoryId, amount: Math.abs(parseFloat(group.value.net_expense || 0)) }], walletId)
  } else {
    await groupStore.clearGroupCategorySplits(group.value.id, walletId)
  }
  await loadGroup()
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

const splitTotal = computed(() => {
  if (!group.value) return 0
  return Math.abs(parseFloat(group.value.net_expense || 0))
})

const splitAllocated = computed(() => splitRows.value.reduce((sum, r) => sum + (r.amount || 0), 0))
const splitRemaining = computed(() => splitTotal.value - splitAllocated.value)
const splitValid = computed(() => {
  return splitRows.value.length >= 2
    && splitRows.value.every((r) => r.id_category != null && r.amount > 0)
    && Math.abs(splitRemaining.value) < 0.01
})

const splitDisplayValues = ref([])

function syncDisplayFromAmounts() {
  const total = splitTotal.value
  if (splitMode.value === 'ratio') {
    splitDisplayValues.value = splitRows.value.map((r) =>
      total > 0 ? Math.round(((r.amount || 0) / total) * 100) : 0
    )
  } else if (splitMode.value === 'parts') {
    splitDisplayValues.value = splitRows.value.map(() => 1)
  }
}

function onDisplayValueChange(idx, val) {
  const total = splitTotal.value
  if (splitMode.value === 'ratio') {
    splitDisplayValues.value[idx] = val
    splitRows.value[idx].amount = Math.round(((val || 0) / 100) * total * 100) / 100
  } else if (splitMode.value === 'parts') {
    splitDisplayValues.value[idx] = val
    const totalParts = splitDisplayValues.value.reduce((s, p) => s + (p || 0), 0)
    if (totalParts > 0) {
      let allocated = 0
      splitRows.value.forEach((row, i) => {
        if (i === splitRows.value.length - 1) {
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
  const splits = group.value?.category_splits || []
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
    onDisplayValueChange(0, splitDisplayValues.value[0])
  }
}

function cancelSplitEdit() {
  splitEditing.value = false
}

async function saveSplits() {
  if (!splitValid.value || !group.value) return
  const splits = splitRows.value.map((r) => ({ id_category: r.id_category, amount: r.amount }))
  await groupStore.setGroupCategorySplits(group.value.id, splits, activeWalletStore.activeWalletId)
  splitEditing.value = false
  await loadGroup()
}

async function clearSplits() {
  if (!group.value) return
  await groupStore.clearGroupCategorySplits(group.value.id, activeWalletStore.activeWalletId)
  splitEditing.value = false
  await loadGroup()
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

watch(() => route.params.id, loadGroup, { immediate: true })
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

    <template v-else-if="group">
      <!-- Group Detail -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <TransactionGroupDetail :group="group" :clickableMembers="true" @select="openTransaction" />
      </div>

      <!-- Category -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactions.category') }}</h3>
        <div v-if="!isMultiCategory">
          <CategorySelect
            :modelValue="currentCategoryId"
            @update:modelValue="onCategoryChanged"
            :placeholder="t('transactions.uncategorized')"
            :showClear="!!currentCategoryId"
            class="w-full max-w-sm"
          />
        </div>
        <div v-else class="flex items-center gap-2 text-sm text-surface-600">
          <i class="pi pi-tags"></i>
          <span>{{ t('transactionDetail.multiCategory', { count: group.category_splits.length }) }}</span>
        </div>
      </div>

      <!-- Category Splits -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4 overflow-hidden">
        <h3 class="text-sm font-semibold mb-3">{{ t('transactionDetail.categorySplits') }}</h3>

        <template v-if="!splitEditing">
          <div v-if="(group.category_splits || []).length >= 2" class="space-y-2 mb-3">
            <div
              v-for="(split, idx) in group.category_splits"
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
          <div v-else-if="(group.category_splits || []).length === 1" class="text-sm text-surface-500 mb-3">
            {{ getCategoryName(group.category_splits[0].id_category) }} — {{ parseFloat(group.category_splits[0].amount).toFixed(2) }}
          </div>

          <div class="flex gap-2">
            <Button
              v-if="(group.category_splits || []).length >= 2"
              :label="t('transactionDetail.editSplits')"
              icon="pi pi-pencil"
              severity="secondary"
              size="small"
              @click="startSplitEdit"
            />
            <Button
              v-if="(group.category_splits || []).length >= 2"
              :label="t('transactionDetail.resetToSingle')"
              icon="pi pi-times"
              severity="warn"
              size="small"
              text
              @click="clearSplits"
            />
            <Button
              v-if="(group.category_splits || []).length < 2"
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
              <InputNumber
                v-if="splitMode === 'amount'"
                v-model="row.amount"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
                inputClass="w-full"
                class="w-24 shrink-0"
              />
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
            <span>{{ t('transactionDetail.splitTotal') }}: {{ splitAllocated.toFixed(2) }} / {{ splitTotal.toFixed(2) }}</span>
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

      <!-- Actions -->
      <div class="bg-surface-0 rounded-xl shadow p-6 mb-4">
        <div class="flex gap-2">
          <Button
            :label="t('transactionDetail.editGroup')"
            icon="pi pi-pencil"
            severity="secondary"
            size="small"
            @click="openGroupDialog"
          />
          <Button
            :label="t('common.delete')"
            icon="pi pi-trash"
            severity="danger"
            size="small"
            text
            @click="deleteGroup"
          />
        </div>
      </div>

      <!-- Group Dialog -->
      <TransactionGroupDialog
        :visible="groupDialogVisible"
        @update:visible="groupDialogVisible = $event"
        :group="group"
        :initialTransaction="null"
        :walletId="activeWalletStore.activeWalletId"
        :walletAccountIds="activeWalletStore.walletAccountIds"
        @saved="onGroupSaved"
        @deleted="onGroupDeleted"
      />
    </template>
  </div>
</template>
