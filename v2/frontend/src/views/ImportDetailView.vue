<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useImportStore } from '../stores/imports'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Drawer from 'primevue/drawer'
import ImportTransactionTable from '../components/imports/ImportTransactionTable.vue'
import FlowDetailPanel from '../components/flow/FlowDetailPanel.vue'
import DataTable from 'primevue/datatable'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const importStore = useImportStore()

const loading = ref(true)
const selectedTx = ref(null)
const drawerVisible = computed({
  get: () => selectedTx.value !== null,
  set: (v) => { if (!v) selectedTx.value = null },
})

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString()
}

function selectTransaction(txId) {
  selectedTx.value = txId
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    await Promise.all([
      importStore.fetchImport(id),
      importStore.fetchImportTransactions(id),
      importStore.fetchImportDuplicates(id),
      importStore.fetchImportAutoTagged(id),
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
          <Tab value="duplicates">{{ t('import.duplicates') }} ({{ importStore.importDuplicates.length }})</Tab>
          <Tab value="autotagged">{{ t('import.autoTagged') }} ({{ importStore.importAutoTagged.length }})</Tab>
          <Tab value="accounts">{{ t('accounts.title') }} ({{ importStore.importAccounts.length }})</Tab>
          <Tab value="files">{{ t('import.files') }} ({{ importStore.currentImport.filenames?.length || 0 }})</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="transactions">
            <ImportTransactionTable :transactions="importStore.importTransactions" @select="selectTransaction">
              <Column :header="t('transactions.category')" style="width: 140px">
                <template #body="{ data }">
                  <Tag v-if="data.category_splits?.length" :value="data.category_splits[0].category?.name" :style="{ backgroundColor: data.category_splits[0].category?.color, color: '#fff' }" />
                  <span v-else class="text-surface-400">—</span>
                </template>
              </Column>
            </ImportTransactionTable>
          </TabPanel>
          <TabPanel value="duplicates">
            <ImportTransactionTable :transactions="importStore.importDuplicates" :emptyMessage="t('import.noDuplicates')" @select="selectTransaction">
              <Column :header="t('import.duplicateOf')" style="width: 120px">
                <template #body="{ data }">
                  <span v-if="data.id_duplicate_of" class="text-sm text-surface-500">#{{ data.id_duplicate_of }}</span>
                  <span v-else class="text-surface-400">—</span>
                </template>
              </Column>
            </ImportTransactionTable>
          </TabPanel>
          <TabPanel value="autotagged">
            <ImportTransactionTable :transactions="importStore.importAutoTagged" :emptyMessage="t('import.noAutoTagged')" @select="selectTransaction">
              <Column :header="t('transactions.category')" style="width: 140px">
                <template #body="{ data }">
                  <Tag v-if="data.category_splits?.length" :value="data.category_splits[0].category?.name" :style="{ backgroundColor: data.category_splits[0].category?.color, color: '#fff' }" />
                  <span v-else class="text-surface-400">—</span>
                </template>
              </Column>
            </ImportTransactionTable>
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

    <Drawer v-model:visible="drawerVisible" position="right" :header="t('flow.transactionDetail')" :style="{ width: '36rem' }">
      <FlowDetailPanel
        v-if="selectedTx"
        :transactionId="selectedTx"
        @back="selectedTx = null"
      />
    </Drawer>
  </div>
</template>
