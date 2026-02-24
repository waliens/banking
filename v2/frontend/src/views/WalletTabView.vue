<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import { useActiveWalletStore } from '../stores/activeWallet'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import IncomeExpenseChart from '../components/analytics/IncomeExpenseChart.vue'
import CategoryChart from '../components/analytics/CategoryChart.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'

const { t } = useI18n()
const walletStore = useWalletStore()
const activeWalletStore = useActiveWalletStore()

const walletId = computed(() => activeWalletStore.activeWalletId)
const wallet = computed(() => activeWalletStore.activeWallet)

const walletOptions = computed(() =>
  walletStore.wallets.map((w) => ({ label: w.name, value: w.id })),
)

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

function onWalletChange(id) {
  activeWalletStore.setActiveWallet(id)
}

async function loadAllStats() {
  if (!walletId.value) return
  await Promise.all([loadBalance(), loadIncomeExpense(), loadPerCategory()])
}

async function loadBalance() {
  if (!walletId.value) return
  await walletStore.fetchBalance(walletId.value)
}

async function loadIncomeExpense() {
  if (!walletId.value) return
  await walletStore.fetchIncomeExpense(walletId.value, { year: selectedYear.value })
}

async function loadPerCategory() {
  if (!walletId.value) return
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

watch(walletId, loadAllStats)
watch(selectedYear, loadIncomeExpense)
watch([categoryDateFrom, categoryDateTo, incomeOnly], loadPerCategory)

onMounted(async () => {
  if (!walletStore.wallets.length) {
    await walletStore.fetchWallets()
  }
  await loadAllStats()
})
</script>

<template>
  <div>
    <!-- Header with wallet switcher -->
    <div class="flex items-center gap-3 mb-6">
      <div class="flex-1">
        <h1 class="text-2xl font-bold">{{ wallet?.name || t('nav.wallet') }}</h1>
        <p v-if="wallet?.description" class="text-sm text-surface-500">{{ wallet.description }}</p>
      </div>
      <Select
        :modelValue="walletId"
        @update:modelValue="onWalletChange"
        :options="walletOptions"
        optionLabel="label"
        optionValue="value"
        :placeholder="t('wallet.selectWallet')"
        class="w-48"
      />
    </div>

    <!-- Empty state -->
    <div v-if="!walletId" class="text-center py-16 text-surface-400">
      <i class="pi pi-briefcase text-5xl mb-4 block" />
      <h2 class="text-xl font-semibold mb-2">{{ t('wallet.noWalletSelected') }}</h2>
      <p class="mb-4">{{ t('wallet.createFirst') }}</p>
      <div class="flex justify-center gap-3 mb-4">
        <router-link to="/import">
          <Button :label="t('nav.import')" icon="pi pi-upload" />
        </router-link>
        <router-link to="/settings">
          <Button :label="t('nav.wallet')" icon="pi pi-plus" />
        </router-link>
      </div>
    </div>

    <template v-else>
      <!-- Stats tabs -->
      <Tabs value="income-expense">
        <TabList>
          <Tab value="income-expense">{{ t('wallet.incomeExpense') }}</Tab>
          <Tab value="per-category">{{ t('wallet.perCategory') }}</Tab>
          <Tab value="balance">{{ t('wallet.balance') }}</Tab>
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
          <TabPanel value="balance">
            <div class="mt-2">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div
                  v-for="account in walletStore.balance?.accounts || []"
                  :key="account.id"
                  class="bg-surface-0 rounded-xl shadow p-4"
                >
                  <AccountDisplay :account="account" />
                  <div class="text-xl font-bold mt-1">
                    <CurrencyDisplay
                      :amount="account.balance"
                      :currencySymbol="account.currency_symbol"
                    />
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
          </TabPanel>
        </TabPanels>
      </Tabs>
    </template>
  </div>
</template>
