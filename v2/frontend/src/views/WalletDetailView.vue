<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import Button from 'primevue/button'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import IncomeExpenseChart from '../components/analytics/IncomeExpenseChart.vue'
import CategoryChart from '../components/analytics/CategoryChart.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const walletStore = useWalletStore()

const walletId = computed(() => Number(route.params.id))
const wallet = computed(() => walletStore.wallets.find((w) => w.id === walletId.value))

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)
const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 5; y--) {
    years.push({ label: String(y), value: y })
  }
  return years
})

const categoryDateFrom = ref(null)
const categoryDateTo = ref(null)
const incomeOnly = ref(false)

async function loadBalance() {
  await walletStore.fetchBalance(walletId.value)
}

async function loadIncomeExpense() {
  await walletStore.fetchIncomeExpense(walletId.value, { year: selectedYear.value })
}

async function loadPerCategory() {
  const params = { income_only: incomeOnly.value }
  if (categoryDateFrom.value) {
    params.date_from = formatDate(categoryDateFrom.value)
  }
  if (categoryDateTo.value) {
    params.date_to = formatDate(categoryDateTo.value)
  }
  await walletStore.fetchPerCategory(walletId.value, params)
}

function formatDate(d) {
  if (!d) return null
  const dt = new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

watch(selectedYear, loadIncomeExpense)
watch([categoryDateFrom, categoryDateTo, incomeOnly], loadPerCategory)

onMounted(async () => {
  if (!walletStore.wallets.length) {
    await walletStore.fetchWallets()
  }
  await Promise.all([loadBalance(), loadIncomeExpense(), loadPerCategory()])
})
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <Button icon="pi pi-arrow-left" text rounded @click="router.push('/wallets')" />
      <div>
        <h1 class="text-2xl font-bold">{{ wallet?.name || t('common.loading') }}</h1>
        <p v-if="wallet?.description" class="text-sm text-surface-500">{{ wallet.description }}</p>
      </div>
    </div>

    <!-- Balance cards -->
    <div class="mb-6">
      <h2 class="text-lg font-semibold mb-3">{{ t('wallet.balance') }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div
          v-for="account in walletStore.balance?.accounts || []"
          :key="account.id"
          class="bg-surface-0 rounded-xl shadow p-4"
        >
          <div class="text-sm text-surface-500">{{ account.name || account.number }}</div>
          <div class="text-xl font-bold mt-1">
            {{ Number(account.balance).toLocaleString('en', { minimumFractionDigits: 2 }) }}
            {{ account.currency_symbol }}
          </div>
        </div>
      </div>
      <p
        v-if="walletStore.balance && !walletStore.balance.accounts?.length"
        class="text-surface-500"
      >
        {{ t('wallet.noData') }}
      </p>
    </div>

    <!-- Stats tabs -->
    <Tabs value="income-expense">
      <TabList>
        <Tab value="income-expense">{{ t('wallet.incomeExpense') }}</Tab>
        <Tab value="per-category">{{ t('wallet.perCategory') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="income-expense">
          <div class="flex items-center gap-3 mb-4 mt-2">
            <label class="text-sm font-medium">{{ t('wallet.year') }}</label>
            <Select
              v-model="selectedYear"
              :options="yearOptions"
              optionLabel="label"
              optionValue="value"
              class="w-32"
            />
          </div>
          <IncomeExpenseChart :data="walletStore.incomeExpense" />
        </TabPanel>
        <TabPanel value="per-category">
          <div class="flex flex-wrap items-center gap-3 mb-4 mt-2">
            <label class="text-sm font-medium">{{ t('wallet.dateRange') }}</label>
            <DatePicker v-model="categoryDateFrom" dateFormat="yy-mm-dd" :placeholder="t('transactions.date')" showIcon class="w-40" />
            <span class="text-surface-500">-</span>
            <DatePicker v-model="categoryDateTo" dateFormat="yy-mm-dd" :placeholder="t('transactions.date')" showIcon class="w-40" />
            <Button
              :label="incomeOnly ? t('wallet.income') : t('wallet.expense')"
              :severity="incomeOnly ? 'success' : 'danger'"
              size="small"
              outlined
              @click="incomeOnly = !incomeOnly"
            />
          </div>
          <CategoryChart :data="walletStore.perCategory" />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>
