<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useImportStore } from '../stores/imports'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const importStore = useImportStore()

const loading = ref(true)

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString()
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    await Promise.all([
      importStore.fetchImport(id),
      importStore.fetchImportTransactions(id),
      importStore.fetchImportAccounts(id),
    ])
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <Button
      :label="t('import.backToImports')"
      icon="pi pi-arrow-left"
      text
      size="small"
      class="mb-4"
      @click="router.push('/import')"
    />

    <div v-if="loading" class="flex items-center justify-center py-12">
      <i class="pi pi-spinner pi-spin text-2xl text-surface-400"></i>
    </div>

    <template v-else-if="importStore.currentImport">
      <h1 class="text-2xl font-bold mb-4">
        {{ t('import.importDetail') }}
        <Tag :value="importStore.currentImport.format" class="ml-2" />
      </h1>

      <!-- Stats cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-surface-0 rounded-xl shadow p-4 text-center">
          <div class="text-2xl font-bold text-primary-500">{{ importStore.currentImport.new_transactions }}</div>
          <div class="text-xs text-surface-500 mt-1">{{ t('import.newTransactions') }}</div>
        </div>
        <div class="bg-surface-0 rounded-xl shadow p-4 text-center">
          <div class="text-2xl font-bold text-orange-500">{{ importStore.currentImport.duplicate_transactions }}</div>
          <div class="text-xs text-surface-500 mt-1">{{ t('import.duplicates') }}</div>
        </div>
        <div class="bg-surface-0 rounded-xl shadow p-4 text-center">
          <div class="text-2xl font-bold text-surface-400">{{ importStore.currentImport.skipped_transactions }}</div>
          <div class="text-xs text-surface-500 mt-1">{{ t('import.skipped') }}</div>
        </div>
        <div class="bg-surface-0 rounded-xl shadow p-4 text-center">
          <div class="text-2xl font-bold text-green-500">{{ importStore.currentImport.auto_tagged }}</div>
          <div class="text-xs text-surface-500 mt-1">{{ t('import.autoTagged') }}</div>
        </div>
      </div>

      <div class="text-sm text-surface-500 mb-4">
        {{ formatDateTime(importStore.currentImport.created_at) }}
        <span v-if="importStore.currentImport.date_earliest">
          &mdash; {{ t('import.dateRange') }}: {{ importStore.currentImport.date_earliest }} — {{ importStore.currentImport.date_latest }}
        </span>
      </div>

      <Tabs value="transactions">
        <TabList>
          <Tab value="transactions">{{ t('transactions.title') }} ({{ importStore.importTransactions.length }})</Tab>
          <Tab value="accounts">{{ t('accounts.title') }} ({{ importStore.importAccounts.length }})</Tab>
          <Tab value="files">{{ t('import.files') }} ({{ importStore.currentImport.filenames?.length || 0 }})</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="transactions">
            <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
              <DataTable
                :value="importStore.importTransactions"
                stripedRows
                class="text-sm"
              >
                <Column field="date" :header="t('transactions.date')" style="width: 110px" />
                <Column field="description" :header="t('transactions.description')" />
                <Column :header="t('transactions.source')" style="width: 150px">
                  <template #body="{ data }">
                    <AccountDisplay :account="data.source" />
                  </template>
                </Column>
                <Column :header="t('transactions.amount')" style="width: 120px">
                  <template #body="{ data }">
                    <CurrencyDisplay
                      :amount="data.amount"
                      :currencySymbol="data.currency?.symbol || ''"
                      :showSign="true"
                      colored
                      class="font-medium"
                    />
                  </template>
                </Column>
                <Column :header="t('transactions.category')" style="width: 140px">
                  <template #body="{ data }">
                    <Tag v-if="data.category" :value="data.category.name" :style="{ backgroundColor: data.category.color, color: '#fff' }" />
                    <span v-else class="text-surface-400">—</span>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>
          <TabPanel value="accounts">
            <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
              <DataTable :value="importStore.importAccounts" stripedRows class="text-sm">
                <Column field="name" header="Name" />
                <Column field="number" header="Number">
                  <template #body="{ data }">
                    <code class="text-xs">{{ data.number || '—' }}</code>
                  </template>
                </Column>
                <Column field="institution" header="Institution">
                  <template #body="{ data }">
                    <Tag v-if="data.institution" :value="data.institution" />
                    <span v-else class="text-surface-400">—</span>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>
          <TabPanel value="files">
            <div class="bg-surface-0 rounded-xl shadow p-4">
              <ul class="space-y-2">
                <li
                  v-for="(filename, idx) in importStore.currentImport.filenames"
                  :key="idx"
                  class="flex items-center gap-2 text-sm"
                >
                  <i class="pi pi-file text-surface-400"></i>
                  {{ filename }}
                </li>
              </ul>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </template>
  </div>
</template>
