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
import Tag from 'primevue/tag'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountSelect from '../components/common/AccountSelect.vue'
import CategorySelect from '../components/common/CategorySelect.vue'
import { contrastText } from '../utils/color'
import { formatDate } from '../utils/date'

const { t } = useI18n()
const transactionStore = useTransactionStore()
const categoryStore = useCategoryStore()
const accountStore = useAccountStore()
const mlStore = useMLStore()
const activeWalletStore = useActiveWalletStore()

const page = ref(0)
const pageSize = ref(50)
const filtersVisible = ref(false)

// Mixed list of transactions and groups for the table
const tableRows = ref([])

// Staged (pending) category selections — not yet committed to backend
const pendingCategories = ref({})

function isPending(rowKey) {
  return rowKey in pendingCategories.value
}

function displayCategoryId(row) {
  const key = rowKey(row)
  if (isPending(key)) return pendingCategories.value[key]
  const splits = row._type === 'group' ? row.category_splits : row.category_splits
  return splits && splits.length === 1 ? splits[0].id_category : null
}

function isMultiCategory(row) {
  const key = rowKey(row)
  if (isPending(key)) return false
  const splits = row._type === 'group' ? row.category_splits : row.category_splits
  return splits && splits.length > 1
}

function rowKey(row) {
  return row._type === 'group' ? `g-${row.id}` : `t-${row.id}`
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
    exclude_grouped: true,
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

async function loadData() {
  const walletId = activeWalletStore.activeWalletId

  // Fetch transactions and unreviewed groups in parallel
  const promises = [transactionStore.fetchTransactions(buildParams())]
  if (walletId && !showReviewed.value && !showLabeled.value) {
    promises.push(transactionStore.fetchUnreviewedGroups(walletId))
  } else {
    promises.push(Promise.resolve([]))
  }

  const [, groups] = await Promise.all(promises)

  // Build mixed table rows
  const txRows = transactionStore.transactions.map(tx => ({
    ...tx,
    _type: 'transaction',
    _key: `t-${tx.id}`,
    _displayDate: tx.date,
    _displayDescription: tx.description || '—',
  }))

  const groupRows = (groups || []).map(g => ({
    ...g,
    _type: 'group',
    _key: `g-${g.id}`,
    _displayDate: g.transactions?.length > 0
      ? g.transactions.map(tx => tx.date).sort().reverse()[0]
      : '',
    _displayDescription: g.name || t('review.groupBadge'),
  }))

  // Groups first, then transactions
  tableRows.value = [...groupRows, ...txRows]

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

function onCategoryStaged(row, categoryId) {
  const key = rowKey(row)
  if (categoryId === null) {
    if (row._type === 'transaction') {
      transactionStore.setCategory(row.id, null).then(() => refreshAfterAction())
    }
    delete pendingCategories.value[key]
  } else {
    pendingCategories.value[key] = categoryId
  }
}

async function commitCategory(row) {
  const key = rowKey(row)
  const categoryId = pendingCategories.value[key]
  if (row._type === 'group') {
    const walletId = activeWalletStore.activeWalletId
    if (walletId) await transactionStore.setGroupCategory(row.id, categoryId, walletId)
  } else {
    await transactionStore.setCategory(row.id, categoryId)
  }
  delete pendingCategories.value[key]
  await refreshAfterAction()
}

async function commitAllPending() {
  const entries = Object.entries(pendingCategories.value)
  if (!entries.length) return

  // Separate transaction and group entries
  const txEntries = entries.filter(([k]) => k.startsWith('t-'))
  const groupEntries = entries.filter(([k]) => k.startsWith('g-'))

  // Batch commit transactions
  if (txEntries.length > 0) {
    const categories = Object.fromEntries(
      txEntries.map(([k, v]) => [k.slice(2), v]).filter(([, v]) => v !== null)
    )
    if (Object.keys(categories).length) await transactionStore.tagBatch(categories)
  }

  // Commit groups one by one
  const walletId = activeWalletStore.activeWalletId
  for (const [k, v] of groupEntries) {
    if (v !== null && walletId) {
      const groupId = Number(k.slice(2))
      await transactionStore.setGroupCategory(groupId, v, walletId)
    }
  }

  pendingCategories.value = {}
  await refreshAfterAction()
}

async function markReviewed(row) {
  if (row._type === 'group') {
    const walletId = activeWalletStore.activeWalletId
    if (walletId) await transactionStore.reviewGroup(row.id, walletId)
  } else {
    await transactionStore.reviewTransaction(row.id)
  }
  await refreshAfterAction()
}

async function markAllReviewed() {
  // Mark all transactions
  const txIds = tableRows.value.filter(r => r._type === 'transaction').map(r => r.id)
  if (txIds.length > 0) {
    await transactionStore.reviewBatch(txIds)
  }

  // Mark all groups
  const walletId = activeWalletStore.activeWalletId
  const groupRows = tableRows.value.filter(r => r._type === 'group')
  for (const g of groupRows) {
    if (walletId) await transactionStore.reviewGroup(g.id, walletId)
  }

  await refreshAfterAction()
}

async function applyBatchTag() {
  if (!batchCategoryId.value) return

  const walletId = activeWalletStore.activeWalletId

  // Batch tag transactions
  const txCategories = {}
  tableRows.value.filter(r => r._type === 'transaction').forEach((row) => {
    txCategories[row.id] = batchCategoryId.value
  })
  if (Object.keys(txCategories).length > 0) {
    await transactionStore.tagBatch(txCategories)
  }

  // Tag groups
  const groupRows = tableRows.value.filter(r => r._type === 'group')
  for (const g of groupRows) {
    if (walletId) await transactionStore.setGroupCategory(g.id, batchCategoryId.value, walletId)
  }

  batchCategoryId.value = null
  await refreshAfterAction()
}

async function refreshAfterAction() {
  await Promise.all([loadData(), transactionStore.fetchReviewCount()])
}

async function openDrawer(row) {
  if (row._type === 'group') return // No drawer for groups
  drawerLoading.value = true
  drawerVisible.value = true
  try {
    const data = await transactionStore.fetchTransaction(row.id)
    selectedTransaction.value = data
  } finally {
    drawerLoading.value = false
  }
}

function onDrawerCategoryChanged() {
  refreshAfterAction()
  if (selectedTransaction.value) {
    openDrawer(selectedTransaction.value)
  }
}

// Negate for expenses (wallet account is source), keep positive for income (wallet account is dest)
function displayAmount(row) {
  if (row._type === 'group') {
    return -row.net_expense
  }
  if (isWalletAccount(row.dest)) return row.amount
  return -row.amount
}

function rowCurrency(row) {
  if (row._type === 'group') {
    return row.transactions?.[0]?.currency?.symbol || ''
  }
  return row.currency?.symbol || ''
}

function isWalletAccount(account) {
  if (!account) return false
  return activeWalletStore.walletAccountIds.includes(account.id)
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
          :disabled="tableRows.length === 0"
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
          :disabled="!batchCategoryId || tableRows.length === 0"
          @click="applyBatchTag"
        />
      </div>
    </div>

    <div v-if="!transactionStore.loading && tableRows.length === 0" class="text-center py-12 text-surface-400">
      <i class="pi pi-check-circle text-4xl mb-3 block" />
      <p>{{ t('review.empty') }}</p>
    </div>

    <div v-else class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        :value="tableRows"
        :loading="transactionStore.loading"
        :lazy="true"
        :paginator="true"
        :rows="pageSize"
        :totalRecords="transactionStore.totalCount + tableRows.filter(r => r._type === 'group').length"
        @page="onPage"
        @row-click="(e) => openDrawer(e.data)"
        dataKey="_key"
        stripedRows
        responsiveLayout="scroll"
        class="text-sm cursor-pointer"
      >
        <Column field="_displayDate" :header="t('transactions.date')" style="width: 110px">
          <template #body="{ data }">
            <div class="flex items-center gap-2">
              <Tag v-if="data._type === 'group'" value="Group" severity="info" class="text-[10px] px-1.5 py-0.5" />
              <span>{{ data._displayDate }}</span>
            </div>
          </template>
        </Column>

        <Column field="_displayDescription" :header="t('transactions.description')">
          <template #body="{ data }">
            <div>
              <span v-tooltip.top="data._displayDescription" class="truncate block max-w-xs">{{ data._displayDescription }}</span>
              <span v-if="data._type === 'group'" class="text-xs text-surface-400">
                {{ t('tagger.groupTransactions', { count: data.transactions?.length || 0 }) }}
              </span>
            </div>
          </template>
        </Column>

        <Column field="source" :header="t('transactions.source')" style="width: 150px">
          <template #body="{ data }">
            <template v-if="data._type === 'transaction'">
              <AccountDisplay :account="data.source" :highlight="isWalletAccount(data.source)" />
            </template>
            <span v-else class="text-xs text-surface-400">—</span>
          </template>
        </Column>

        <Column field="dest" :header="t('transactions.dest')" style="width: 150px">
          <template #body="{ data }">
            <template v-if="data._type === 'transaction'">
              <AccountDisplay :account="data.dest" :highlight="isWalletAccount(data.dest)" />
            </template>
            <span v-else class="text-xs text-surface-400">—</span>
          </template>
        </Column>

        <Column field="amount" :header="t('transactions.amount')" style="width: 120px">
          <template #body="{ data }">
            <CurrencyDisplay
              :amount="displayAmount(data)"
              :currencySymbol="rowCurrency(data)"
              :showSign="true"
              colored
              class="font-medium"
            />
            <span
              v-if="data._type === 'transaction' && data.effective_amount != null && data.effective_amount !== data.amount"
              class="text-xs text-surface-400 block"
            >
              ({{ t('transactions.effectiveAmount') }}: {{ data.effective_amount }})
            </span>
            <span
              v-if="data._type === 'group'"
              class="text-xs text-surface-400 block"
            >
              {{ t('transactions.totalPaid') }}: {{ data.total_paid }}
            </span>
          </template>
        </Column>

        <Column field="category" :header="t('transactions.category')" style="width: 240px">
          <template #body="{ data }">
            <div @click.stop class="flex items-center gap-1">
              <template v-if="isMultiCategory(data)">
                <div class="flex items-center gap-2 text-sm text-surface-600">
                  <i class="pi pi-tags"></i>
                  <span>{{ t('transactionDetail.multiCategory', { count: data.category_splits.length }) }}</span>
                </div>
              </template>
              <template v-else>
                <div class="flex-1">
                  <div class="flex items-center gap-1">
                    <CategorySelect
                      :modelValue="displayCategoryId(data)"
                      @update:modelValue="(v) => onCategoryStaged(data, v)"
                      :placeholder="t('transactions.uncategorized')"
                      :showClear="!!displayCategoryId(data)"
                      class="flex-1"
                      :class="isPending(rowKey(data)) ? 'ring-1 ring-amber-400 rounded-lg' : ''"
                    />
                    <Button
                      v-if="isPending(rowKey(data))"
                      icon="pi pi-check"
                      severity="success"
                      size="small"
                      text
                      rounded
                      @click="commitCategory(data)"
                      v-tooltip.top="t('review.saveTag')"
                    />
                  </div>
                  <div v-if="data._type === 'transaction' && mlStore.predictions[data.id] && !displayCategoryId(data)" class="mt-1">
                    <button
                      class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer hover:opacity-80 transition-opacity"
                      :style="{
                        backgroundColor: (mlStore.predictions[data.id].category_color || '#6366f1') + '20',
                        color: contrastText(mlStore.predictions[data.id].category_color || '#6366f1'),
                        border: `1px solid ${mlStore.predictions[data.id].category_color || '#6366f1'}40`,
                      }"
                      @click="acceptSuggestion(data.id, mlStore.predictions[data.id].category_id)"
                    >
                      <i class="pi pi-sparkles text-[10px]" />
                      <span>AI: {{ mlStore.predictions[data.id].category_name }}</span>
                      <span class="opacity-60">{{ Math.round(mlStore.predictions[data.id].probability * 100) }}%</span>
                    </button>
                  </div>
                </div>
              </template>
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
                @click="markReviewed(data)"
              />
            </div>
          </template>
        </Column>

      </DataTable>
    </div>

    <!-- Transaction Detail Drawer -->
    <Drawer v-model:visible="drawerVisible" position="right" :header="t('review.transactionDetail')" :style="{ width: '36rem' }">
      <div v-if="drawerLoading" class="flex items-center justify-center py-12">
        <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
      </div>
      <template v-else-if="selectedTransaction">
        <router-link :to="`/transactions/${selectedTransaction.id}`" class="block mb-4">
          <Button :label="t('transactionDetail.openFullPage')" icon="pi pi-external-link" severity="secondary" size="small" text />
        </router-link>
        <TransactionDetail
          :transaction="selectedTransaction"
          @categoryChanged="onDrawerCategoryChanged"
        />
      </template>
    </Drawer>
  </div>
</template>
