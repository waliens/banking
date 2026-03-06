<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useWalletStore } from '../../stores/wallets'
import { useCategoryStore } from '../../stores/categories'
import SelectButton from 'primevue/selectbutton'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import PeriodFilter from './PeriodFilter.vue'
import CategorySelect from '../common/CategorySelect.vue'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'
import { formatDate, getDateRange } from '../../utils/date'

const props = defineProps({
  walletId: { type: Number, required: true },
})

const { t } = useI18n()
const router = useRouter()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

// Period controls
const periodBucket = ref('month')
const periodType = ref('year')
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const dateFrom = ref(null)
const dateTo = ref(null)

// View controls
const hideEmpty = ref(true)
const expandedParents = ref(new Set())
const selectedCategoryIds = ref([])

// Data
const expenseData = ref(null)
const incomeData = ref(null)

const bucketOptions = [
  { label: t('wallet.monthly'), value: 'month' },
  { label: t('wallet.yearly'), value: 'year' },
]

function computeDateRange() {
  return getDateRange({
    periodType: periodType.value,
    year: year.value,
    month: month.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  })
}

async function loadData() {
  if (!props.walletId) return
  const { date_from, date_to } = computeDateRange()
  const params = { date_from, date_to, period_bucket: periodBucket.value }
  const [expense, income] = await Promise.all([
    walletStore.fetchPerCategoryTable(props.walletId, { ...params, income_only: false }),
    walletStore.fetchPerCategoryTable(props.walletId, { ...params, income_only: true }),
  ])
  expenseData.value = expense
  incomeData.value = income
}

// Periods: sorted descending
const periods = computed(() => {
  const allItems = [...(expenseData.value?.items || []), ...(incomeData.value?.items || [])]
  const periodSet = new Set()
  for (const item of allItems) {
    if (periodBucket.value === 'month' && item.period_year != null && item.period_month != null) {
      periodSet.add(`${item.period_year}-${String(item.period_month).padStart(2, '0')}`)
    } else if (item.period_year != null) {
      periodSet.add(String(item.period_year))
    }
  }
  return [...periodSet].sort().reverse()
})

// Build category->period->net amount matrix
const categoryMatrix = computed(() => {
  const matrix = new Map() // categoryId -> Map(period -> net)

  function addToMatrix(items, sign) {
    for (const item of items || []) {
      const catId = item.id_category ?? '__uncategorized__'
      let period
      if (periodBucket.value === 'month') {
        period = `${item.period_year}-${String(item.period_month).padStart(2, '0')}`
      } else {
        period = String(item.period_year)
      }
      if (!matrix.has(catId)) matrix.set(catId, new Map())
      const current = matrix.get(catId).get(period) || 0
      matrix.get(catId).set(period, current + sign * Number(item.amount))
    }
  }

  // Expenses are negative, income is positive
  addToMatrix(expenseData.value?.items, -1)
  addToMatrix(incomeData.value?.items, 1)
  return matrix
})

// Build hierarchical rows
const tableRows = computed(() => {
  const tree = categoryStore.categoryTree
  const rows = []
  const selectedSet = new Set(selectedCategoryIds.value)

  for (const parent of tree) {
    const childRows = []
    let parentTotals = new Map() // period -> sum

    const children = parent.children || []
    let hasVisibleChild = false

    for (const child of children) {
      const amounts = categoryMatrix.value.get(child.id)
      const hasData = amounts && amounts.size > 0
      if (hideEmpty.value && !hasData) continue
      if (!selectedSet.has(child.id)) continue

      hasVisibleChild = true
      childRows.push({
        id: child.id,
        name: child.name,
        color: child.color,
        icon: child.icon,
        isParent: false,
        amounts: amounts || new Map(),
      })

      // Sum into parent
      if (amounts) {
        for (const [period, amount] of amounts) {
          parentTotals.set(period, (parentTotals.get(period) || 0) + amount)
        }
      }
    }

    // Also check if parent itself has direct transactions
    const parentAmounts = categoryMatrix.value.get(parent.id)
    if (parentAmounts) {
      for (const [period, amount] of parentAmounts) {
        parentTotals.set(period, (parentTotals.get(period) || 0) + amount)
      }
    }

    const parentHasData = parentTotals.size > 0
    if (hideEmpty.value && !parentHasData && !hasVisibleChild) continue
    if (!hasVisibleChild && !selectedSet.has(parent.id)) continue

    rows.push({
      id: parent.id,
      name: parent.name,
      color: parent.color,
      icon: parent.icon,
      isParent: true,
      amounts: parentTotals,
      children: childRows,
    })
  }

  // Uncategorized row
  const uncatAmounts = categoryMatrix.value.get('__uncategorized__')
  if (uncatAmounts && uncatAmounts.size > 0) {
    rows.push({
      id: '__uncategorized__',
      name: t('wallet.uncategorized'),
      color: null,
      icon: null,
      isParent: false,
      amounts: uncatAmounts,
      children: [],
    })
  }

  return rows
})

// Totals per period
const periodTotals = computed(() => {
  const totals = new Map()
  for (const row of tableRows.value) {
    for (const [period, amount] of row.amounts) {
      totals.set(period, (totals.get(period) || 0) + amount)
    }
  }
  return totals
})

// Categories available for filter (excludes truly empty ones)
const filterCategories = computed(() => {
  return categoryStore.categoryTree
    .map((parent) => ({
      ...parent,
      children: (parent.children || []).filter((child) => {
        if (!hideEmpty.value) return true
        const amounts = categoryMatrix.value.get(child.id)
        return amounts && amounts.size > 0
      }),
    }))
    .filter((parent) => parent.children.length > 0)
})

// Initialize selected categories
watch([filterCategories, () => expenseData.value, () => incomeData.value], () => {
  const ids = []
  for (const parent of filterCategories.value) {
    ids.push(parent.id)
    for (const child of parent.children) {
      ids.push(child.id)
    }
  }
  selectedCategoryIds.value = ids
}, { immediate: true })

function toggleParent(parentId) {
  const s = new Set(expandedParents.value)
  if (s.has(parentId)) {
    s.delete(parentId)
  } else {
    s.add(parentId)
  }
  expandedParents.value = s
}

function expandAll() {
  expandedParents.value = new Set(tableRows.value.filter((r) => r.isParent).map((r) => r.id))
}

function collapseAll() {
  expandedParents.value = new Set()
}

function isExpanded(parentId) {
  return expandedParents.value.has(parentId)
}

function formatAmount(val) {
  if (val == null || val === 0) return '—'
  return val.toFixed(2)
}

function amountClass(val) {
  if (val > 0) return 'text-green-600'
  if (val < 0) return 'text-red-600'
  return 'text-surface-400'
}

watch(() => props.walletId, loadData)
onMounted(async () => {
  if (!categoryStore.categories.length) {
    await categoryStore.fetchCategories()
  }
  await loadData()
})

function onPeriodChange() {
  loadData()
}

function onBucketChange() {
  loadData()
}

function periodDateRange(period) {
  if (periodBucket.value === 'month') {
    // period = "2024-06"
    const [y, m] = period.split('-').map(Number)
    const lastDay = new Date(y, m, 0).getDate()
    return {
      date_from: `${y}-${String(m).padStart(2, '0')}-01`,
      date_to: `${y}-${String(m).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`,
    }
  }
  // period = "2024"
  return { date_from: `${period}-01-01`, date_to: `${period}-12-31` }
}

function navigateToCategory(categoryId, categoryName, period, amount) {
  if (amount == null || amount === 0) return
  const { date_from, date_to } = periodDateRange(period)
  const query = {
    wallet: props.walletId,
    date_from,
    date_to,
    period_label: period,
  }
  if (categoryId !== '__uncategorized__' && categoryId != null) {
    query.category = categoryId
    query.category_name = categoryName
  } else {
    query.category_name = t('wallet.uncategorized')
  }
  router.push({ name: 'category-transactions', query })
}
</script>

<template>
  <div>
    <!-- Controls -->
    <div class="flex flex-wrap items-center gap-3 mb-4 mt-2">
      <SelectButton
        v-model="periodBucket"
        :options="bucketOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
        @update:modelValue="onBucketChange"
      />
      <PeriodFilter
        v-model:periodType="periodType"
        v-model:year="year"
        v-model:month="month"
        v-model:dateFrom="dateFrom"
        v-model:dateTo="dateTo"
        :showMonthOption="false"
        @change="onPeriodChange"
      />
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-4">
      <Button :label="t('wallet.expandAll')" icon="pi pi-plus" size="small" text @click="expandAll" />
      <Button :label="t('wallet.collapseAll')" icon="pi pi-minus" size="small" text @click="collapseAll" />
      <div class="flex items-center gap-2">
        <ToggleSwitch v-model="hideEmpty" />
        <label class="text-sm">{{ t('wallet.hideEmpty') }}</label>
      </div>
      <div class="max-w-xs">
        <CategorySelect
          v-model="selectedCategoryIds"
          :multiple="true"
          :categories="filterCategories"
          :placeholder="t('categories.selectCategory')"
          :showClear="true"
        />
      </div>
    </div>

    <!-- Table -->
    <div v-if="periods.length && tableRows.length" class="overflow-x-auto border border-surface-200 rounded-lg">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-50">
            <th class="sticky left-0 z-10 bg-surface-50 text-left px-3 py-2 border-b border-surface-200 min-w-[200px]">
              {{ t('transactions.category') }}
            </th>
            <th
              v-for="period in periods"
              :key="period"
              class="sticky top-0 text-right px-3 py-2 border-b border-surface-200 whitespace-nowrap min-w-[100px]"
            >
              {{ period }}
            </th>
          </tr>
          <!-- Total row -->
          <tr class="bg-surface-100 font-bold">
            <td class="sticky left-0 z-10 bg-surface-100 px-3 py-1.5 border-b border-surface-200">
              {{ t('wallet.total') }}
            </td>
            <td
              v-for="period in periods"
              :key="'total-' + period"
              class="text-right px-3 py-1.5 border-b border-surface-200"
              :class="amountClass(periodTotals.get(period) || 0)"
            >
              {{ formatAmount(periodTotals.get(period) || 0) }}
            </td>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in tableRows" :key="row.id">
            <!-- Parent row -->
            <tr
              v-if="row.isParent"
              class="bg-surface-50 font-semibold cursor-pointer hover:bg-surface-100 transition-colors"
              @click="toggleParent(row.id)"
            >
              <td class="sticky left-0 z-10 bg-surface-50 px-3 py-2 border-b border-surface-100">
                <div class="flex items-center gap-2">
                  <i :class="isExpanded(row.id) ? 'pi pi-chevron-down' : 'pi pi-chevron-right'" class="text-xs text-surface-400" />
                  <i v-if="row.icon" :class="row.icon" class="text-sm" :style="row.color ? { color: row.color } : {}" />
                  <span>{{ row.name }}</span>
                </div>
              </td>
              <td
                v-for="period in periods"
                :key="row.id + '-' + period"
                class="text-right px-3 py-2 border-b border-surface-100"
                :class="[amountClass(row.amounts.get(period) || 0), (row.amounts.get(period) || 0) !== 0 ? 'cursor-pointer hover:bg-surface-100' : '']"
                @click.stop="navigateToCategory(row.id, row.name, period, row.amounts.get(period) || 0)"
              >
                {{ formatAmount(row.amounts.get(period) || 0) }}
              </td>
            </tr>

            <!-- Child rows (when expanded) -->
            <template v-if="row.isParent && isExpanded(row.id)">
              <tr
                v-for="child in row.children"
                :key="child.id"
                class="hover:bg-surface-50 transition-colors"
              >
                <td class="sticky left-0 z-10 bg-surface-0 pl-8 pr-3 py-1.5 border-b border-surface-100">
                  <div class="flex items-center gap-2">
                    <i v-if="child.icon" :class="child.icon" class="text-sm" :style="child.color ? { color: child.color } : {}" />
                    <span>{{ child.name }}</span>
                  </div>
                </td>
                <td
                  v-for="period in periods"
                  :key="child.id + '-' + period"
                  class="text-right px-3 py-1.5 border-b border-surface-100"
                  :class="[amountClass(child.amounts.get(period) || 0), (child.amounts.get(period) || 0) !== 0 ? 'cursor-pointer hover:bg-surface-100' : '']"
                  @click="navigateToCategory(child.id, child.name, period, child.amounts.get(period) || 0)"
                >
                  {{ formatAmount(child.amounts.get(period) || 0) }}
                </td>
              </tr>
            </template>

            <!-- Non-parent rows (uncategorized) -->
            <tr v-if="!row.isParent" class="hover:bg-surface-50 transition-colors">
              <td class="sticky left-0 z-10 bg-surface-0 px-3 py-2 border-b border-surface-100 italic text-surface-500">
                {{ row.name }}
              </td>
              <td
                v-for="period in periods"
                :key="row.id + '-' + period"
                class="text-right px-3 py-2 border-b border-surface-100"
                :class="[amountClass(row.amounts.get(period) || 0), (row.amounts.get(period) || 0) !== 0 ? 'cursor-pointer hover:bg-surface-100' : '']"
                @click="navigateToCategory(row.id, row.name, period, row.amounts.get(period) || 0)"
              >
                {{ formatAmount(row.amounts.get(period) || 0) }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <p v-else class="text-surface-500 text-center py-8">{{ t('wallet.noData') }}</p>
  </div>
</template>
