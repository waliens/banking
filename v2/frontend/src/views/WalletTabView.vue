<script setup>
import { computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../stores/wallets'
import { useActiveWalletStore } from '../stores/activeWallet'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import IncomeExpenseChart from '../components/analytics/IncomeExpenseChart.vue'
import CategoryChart from '../components/analytics/CategoryChart.vue'
import CategoryTable from '../components/analytics/CategoryTable.vue'
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

function onWalletChange(id) {
  activeWalletStore.setActiveWallet(id)
}

async function loadBalance() {
  if (!walletId.value) return
  await walletStore.fetchBalance(walletId.value)
}

watch(walletId, loadBalance)

onMounted(async () => {
  if (!walletStore.wallets.length) {
    await walletStore.fetchWallets()
  }
  await loadBalance()
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
          <Tab value="table">{{ t('wallet.table') }}</Tab>
          <Tab value="balance">{{ t('wallet.balance') }}</Tab>
        </TabList>
        <TabPanels class="overflow-visible">
          <TabPanel value="income-expense">
            <IncomeExpenseChart :walletId="walletId" />
          </TabPanel>
          <TabPanel value="per-category">
            <CategoryChart :walletId="walletId" />
          </TabPanel>
          <TabPanel value="table">
            <CategoryTable :walletId="walletId" />
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
