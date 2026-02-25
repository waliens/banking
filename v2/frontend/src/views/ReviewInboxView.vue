<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../stores/transactions'
import { useCategoryStore } from '../stores/categories'
import { useAccountStore } from '../stores/accounts'
import { useMLStore } from '../stores/ml'
import { useActiveWalletStore } from '../stores/activeWallet'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import DatePicker from 'primevue/datepicker'
import ToggleSwitch from 'primevue/toggleswitch'
import Drawer from 'primevue/drawer'
import DuplicateCandidates from '../components/transactions/DuplicateCandidates.vue'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'
import MLSuggestion from '../components/MLSuggestion.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountSelect from '../components/common/AccountSelect.vue'
import CategorySelect from '../components/common/CategorySelect.vue'

const { t } = useI18n()
const transactionStore = useTransactionStore()
const categoryStore = useCategoryStore()
const accountStore = useAccountStore()
const mlStore = useMLStore()
const activeWalletStore = useActiveWalletStore()

const page = ref(0)
const pageSize = ref(50)
const expandedRows = ref([])
const filtersVisible = ref(false)

// Staged (pending) category selections — not yet committed to backend
const pendingCategories = ref({})

function isPending(txId) {
  return txId in pendingCategories.value
}

function displayCategoryId(data) {
  return isPending(data.id) ? pendingCategories.value[data.id] : data.id_category
}

// Filters
const dateFrom = ref(null)
const dateTo = ref(null)
const amountFrom = ref(null)
const amountTo = ref(null)
const searchQuery = ref('')
const showLabeled = ref(false)
const showReviewed = ref(false)
const accountFrom = ref(null)
const accountTo = ref(null)

// Drawer
const drawerVisible = ref(false)
const selectedTransaction = ref(null)
const drawerLoading = ref(false)

// Batch tag
const batchCategoryId = ref(null)

let debounceTimer = null

function buildParams() {
  const params = {
    start: page.value * pageSize.value,
    count: pageSize.value,
    order: 'desc',
  }

  // Wallet scoping
  const walletId = activeWalletStore.activeWalletId
  if (walletId) {
    params.wallet = walletId
    params.wallet_external_only = true
  }

  // Review/label filters (inverted: show* means include those)
  if (!showReviewed.value) params.is_reviewed = false
  if (!showLabeled.value) params.labeled = false
  params.duplicate_only = false

  if (dateFrom.value) params.date_from = formatDate(dateFrom.value)
  if (dateTo.value) params.date_to = formatDate(dateTo.value)
  if (amountFrom.value != null) params.amount_from = amountFrom.value
  if (amountTo.value != null) params.amount_to = amountTo.value
  if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
  if (accountFrom.value != null) params.account_from = accountFrom.value
  if (accountTo.value != null) params.account_to = accountTo.value

  return params
}

function formatDate(d) {
  if (!d) return null
  const dt = new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

async function loadData() {
  await transactionStore.fetchTransactions(buildParams())
  // Fetch ML predictions for visible transactions
  const ids = transactionStore.transactions.map((t) => t.id)
  if (ids.length > 0) {
    try {
      await mlStore.predictTransactions(ids)
    } catch {
      // ML predictions are optional
    }
  }
}

async function acceptSuggestion(transactionId, categoryId) {
  await transactionStore.setCategory(transactionId, categoryId)
  await refreshAfterAction()
}

function onPage(event) {
  pendingCategories.value = {}
  page.value = event.page
  pageSize.value = event.rows
  loadData()
}

function onCategoryStaged(txId, categoryId) {
  if (categoryId === null) {
    // Clearing is deliberate — commit immediately, clear any pending
    transactionStore.setCategory(txId, null).then(() => refreshAfterAction())
    delete pendingCategories.value[txId]
  } else {
    pendingCategories.value[txId] = categoryId
  }
}

async function commitCategory(txId) {
  await transactionStore.setCategory(txId, pendingCategories.value[txId])
  delete pendingCategories.value[txId]
  await refreshAfterAction()
}

async function commitAllPending() {
  const entries = Object.entries(pendingCategories.value)
  if (!entries.length) return
  const categories = Object.fromEntries(entries.filter(([, v]) => v !== null))
  if (Object.keys(categories).length) await transactionStore.tagBatch(categories)
  pendingCategories.value = {}
  await refreshAfterAction()
}

async function markReviewed(id) {
  await transactionStore.reviewTransaction(id)
  await refreshAfterAction()
}

async function markAllReviewed() {
  const ids = transactionStore.transactions.map((t) => t.id)
  if (ids.length === 0) return
  await transactionStore.reviewBatch(ids)
  await refreshAfterAction()
}

async function applyBatchTag() {
  if (!batchCategoryId.value) return
  const categories = {}
  transactionStore.transactions.forEach((tx) => {
    categories[tx.id] = batchCategoryId.value
  })
  await transactionStore.tagBatch(categories)
  batchCategoryId.value = null
  await refreshAfterAction()
}

async function refreshAfterAction() {
  await Promise.all([loadData(), transactionStore.fetchReviewCount()])
}

function onDuplicateResolved() {
  refreshAfterAction()
}

async function openDrawer(tx) {
  drawerLoading.value = true
  drawerVisible.value = true
  try {
    const data = await transactionStore.fetchTransaction(tx.id)
    selectedTransaction.value = data
  } finally {
    drawerLoading.value = false
  }
}

function onDrawerCategoryChanged() {
  refreshAfterAction()
  // Reload detail
  if (selectedTransaction.value) {
    openDrawer(selectedTransaction.value)
  }
}

function debouncedReload() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 0
    loadData()
  }, 300)
}

// Watch filters
watch([dateFrom, dateTo, amountFrom, amountTo, showLabeled, showReviewed, accountFrom, accountTo], () => {
  pendingCategories.value = {}
  page.value = 0
  loadData()
})

watch(searchQuery, () => {
  pendingCategories.value = {}
  debouncedReload()
})

// Watch active wallet changes
watch(() => activeWalletStore.activeWalletId, () => {
  pendingCategories.value = {}
  page.value = 0
  loadData()
})

onMounted(async () => {
  await Promise.all([loadData(), categoryStore.fetchCategories(), transactionStore.fetchReviewCount(), accountStore.fetchAccounts()])
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">
        {{ t('review.title') }}
        <span v-if="transactionStore.reviewCount > 0" class="text-lg font-normal text-surface-500">
          ({{ transactionStore.reviewCount }})
        </span>
      </h1>
      <div class="flex items-center gap-2">
        <Button
          :label="t('review.filters')"
          :icon="filtersVisible ? 'pi pi-filter-slash' : 'pi pi-filter'"
          severity="secondary"
          size="small"
          outlined
          @click="filtersVisible = !filtersVisible"
        />
        <Button
          :label="t('review.saveAllTags')"
          severity="warn"
          size="small"
          icon="pi pi-check-circle"
          :disabled="Object.keys(pendingCategories).length === 0"
          @click="commitAllPending"
        />
        <Button
          :label="t('review.markAllReviewed')"
          severity="secondary"
          size="small"
          icon="pi pi-check-circle"
          :disabled="transactionStore.transactions.length === 0"
          @click="markAllReviewed"
        />
      </div>
    </div>

    <!-- Collapsible filter panel -->
    <div v-if="filtersVisible" class="bg-surface-0 rounded-xl shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Date range -->
        <div class="min-w-0">
          <label class="block text-xs font-medium text-surface-500 mb-1">{{ t('review.dateRange') }}</label>
          <div class="flex gap-2">
            <DatePicker v-model="dateFrom" dateFormat="yy-mm-dd" placeholder="From" showIcon class="flex-1 min-w-0" />
            <DatePicker v-model="dateTo" dateFormat="yy-mm-dd" placeholder="To" showIcon class="flex-1 min-w-0" />
          </div>
        </div>
        <!-- Amount range -->
        <div class="min-w-0">
          <label class="block text-xs font-medium text-surface-500 mb-1">{{ t('review.amountRange') }}</label>
          <div class="flex gap-3">
            <InputNumber v-model="amountFrom" placeholder="Min" class="flex-1 min-w-0" :minFractionDigits="2" />
            <InputNumber v-model="amountTo" placeholder="Max" class="flex-1 min-w-0" :minFractionDigits="2" />
          </div>
        </div>
      </div>
      <!-- Search (full width) -->
      <div class="mb-4">
        <label class="block text-xs font-medium text-surface-500 mb-1">{{ t('common.search') }}</label>
        <InputText v-model="searchQuery" :placeholder="t('common.search')" class="w-full" />
      </div>
      <!-- Second row with account selects -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Source account -->
        <div class="min-w-0">
          <label class="block text-xs font-medium text-surface-500 mb-1">{{ t('review.accountFrom') }}</label>
          <AccountSelect
            v-model="accountFrom"
            :placeholder="t('review.anyAccount')"
            :showClear="true"
            class="w-full"
          />
        </div>
        <!-- Dest account -->
        <div class="min-w-0">
          <label class="block text-xs font-medium text-surface-500 mb-1">{{ t('review.accountTo') }}</label>
          <AccountSelect
            v-model="accountTo"
            :placeholder="t('review.anyAccount')"
            :showClear="true"
            class="w-full"
          />
        </div>
        <!-- Toggles -->
        <div class="flex flex-col gap-2 min-w-0">
          <div class="flex items-center gap-2">
            <ToggleSwitch v-model="showLabeled" />
            <span class="text-sm">{{ t('review.showLabeled') }}</span>
          </div>
          <div class="flex items-center gap-2">
            <ToggleSwitch v-model="showReviewed" />
            <span class="text-sm">{{ t('review.showReviewed') }}</span>
          </div>
        </div>
      </div>
      <!-- Batch tag -->
      <div class="flex items-center gap-3 mt-4 pt-3 border-t border-surface-100">
        <CategorySelect
          v-model="batchCategoryId"
          :placeholder="t('transactions.category')"
          :showClear="true"
          class="w-60"
        />
        <Button
          :label="t('review.batchTag')"
          icon="pi pi-tags"
          size="small"
          :disabled="!batchCategoryId || transactionStore.transactions.length === 0"
          @click="applyBatchTag"
        />
      </div>
    </div>

    <div v-if="!transactionStore.loading && transactionStore.transactions.length === 0" class="text-center py-12 text-surface-400">
      <i class="pi pi-check-circle text-4xl mb-3 block" />
      <p>{{ t('review.empty') }}</p>
    </div>

    <div v-else class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        v-model:expandedRows="expandedRows"
        :value="transactionStore.transactions"
        :loading="transactionStore.loading"
        :lazy="true"
        :paginator="true"
        :rows="pageSize"
        :totalRecords="transactionStore.totalCount"
        @page="onPage"
        @row-click="(e) => openDrawer(e.data)"
        dataKey="id"
        stripedRows
        responsiveLayout="scroll"
        class="text-sm cursor-pointer"
      >
        <Column expander style="width: 3rem" />

        <Column field="date" :header="t('transactions.date')" style="width: 110px" />

        <Column field="description" :header="t('transactions.description')">
          <template #body="{ data }">
            <span v-tooltip.top="data.description" class="truncate block max-w-xs">{{ data.description || '—' }}</span>
          </template>
        </Column>

        <Column field="source" :header="t('transactions.source')" style="width: 150px">
          <template #body="{ data }">
            <AccountDisplay :account="data.source" />
          </template>
        </Column>

        <Column field="amount" :header="t('transactions.amount')" style="width: 120px">
          <template #body="{ data }">
            <CurrencyDisplay
              :amount="data.amount"
              :currencySymbol="data.currency.symbol || ''"
              :showSign="true"
              colored
              class="font-medium"
            />
            <span
              v-if="data.effective_amount != null && data.effective_amount !== data.amount"
              class="text-xs text-surface-400 block"
            >
              ({{ t('transactions.effectiveAmount') }}: {{ data.effective_amount }})
            </span>
          </template>
        </Column>

        <Column :header="t('ml.suggestion')" style="width: 140px">
          <template #body="{ data }">
            <div @click.stop>
              <MLSuggestion
                v-if="mlStore.predictions[data.id]"
                :categoryName="mlStore.predictions[data.id].category_name"
                :categoryColor="mlStore.predictions[data.id].category_color"
                :probability="mlStore.predictions[data.id].probability"
                @accept="acceptSuggestion(data.id, mlStore.predictions[data.id].category_id)"
              />
            </div>
          </template>
        </Column>

        <Column field="category" :header="t('transactions.category')" style="width: 210px">
          <template #body="{ data }">
            <div @click.stop class="flex items-center gap-1">
              <CategorySelect
                :modelValue="displayCategoryId(data)"
                @update:modelValue="(v) => onCategoryStaged(data.id, v)"
                :placeholder="t('transactions.uncategorized')"
                :showClear="!!displayCategoryId(data)"
                class="flex-1"
                :class="isPending(data.id) ? 'ring-1 ring-amber-400 rounded-lg' : ''"
              />
              <Button
                v-if="isPending(data.id)"
                icon="pi pi-check"
                severity="success"
                size="small"
                text
                rounded
                @click="commitCategory(data.id)"
                v-tooltip.top="t('review.saveTag')"
              />
            </div>
          </template>
        </Column>

        <Column style="width: 120px">
          <template #body="{ data }">
            <div @click.stop>
              <Button
                :label="t('review.markReviewed')"
                severity="secondary"
                size="small"
                text
                @click="markReviewed(data.id)"
              />
            </div>
          </template>
        </Column>

        <template #expansion="{ data }">
          <DuplicateCandidates :transactionId="data.id" @resolved="onDuplicateResolved" />
        </template>
      </DataTable>
    </div>

    <!-- Transaction Detail Drawer -->
    <Drawer v-model:visible="drawerVisible" position="right" :header="t('review.transactionDetail')" class="w-full">
      <div v-if="drawerLoading" class="flex items-center justify-center py-12">
        <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
      </div>
      <TransactionDetail
        v-else-if="selectedTransaction"
        :transaction="selectedTransaction"
        @categoryChanged="onDrawerCategoryChanged"
      />
    </Drawer>
  </div>
</template>
