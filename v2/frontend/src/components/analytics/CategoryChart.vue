<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../../stores/wallets'
import { useCategoryStore } from '../../stores/categories'
import PeriodFilter from './PeriodFilter.vue'
import CategoryPieChart from './CategoryPieChart.vue'
import { formatDate, getDateRange } from '../../utils/date'

const props = defineProps({
  walletId: { type: Number, required: true },
})

const { t } = useI18n()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const periodType = ref('year')
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const dateFrom = ref(null)
const dateTo = ref(null)

const expenseData = ref(null)
const incomeData = ref(null)

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
  const [expense, income] = await Promise.all([
    walletStore.fetchPerCategoryPie(props.walletId, { date_from, date_to, income_only: false }),
    walletStore.fetchPerCategoryPie(props.walletId, { date_from, date_to, income_only: true }),
  ])
  expenseData.value = expense
  incomeData.value = income
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
</script>

<template>
  <div>
    <!-- Period filter -->
    <div class="mb-4 mt-2">
      <PeriodFilter
        v-model:periodType="periodType"
        v-model:year="year"
        v-model:month="month"
        v-model:dateFrom="dateFrom"
        v-model:dateTo="dateTo"
        @change="onPeriodChange"
      />
    </div>

    <!-- Dual pie charts -->
    <div class="space-y-8">
      <CategoryPieChart
        :data="expenseData"
        :title="t('wallet.expense')"
        :categoryTree="categoryStore.categoryTree"
        :categoryMap="categoryStore.categoryMap"
      />
      <CategoryPieChart
        :data="incomeData"
        :title="t('wallet.income')"
        :categoryTree="categoryStore.categoryTree"
        :categoryMap="categoryStore.categoryMap"
      />
    </div>
  </div>
</template>
