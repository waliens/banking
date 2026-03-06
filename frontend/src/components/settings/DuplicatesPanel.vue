<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../../stores/transactions'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'
import AccountDisplay from '../common/AccountDisplay.vue'

const { t } = useI18n()
const toast = useToast()
const transactionStore = useTransactionStore()

const duplicates = ref([])
const loading = ref(false)
const expandedRows = ref([])
const originals = ref({})
const page = ref(0)
const pageSize = ref(20)
const totalCount = ref(0)
const searchQuery = ref('')

async function loadDuplicates() {
  loading.value = true
  try {
    const params = {
      start: page.value * pageSize.value,
      count: pageSize.value,
      order: 'desc',
      duplicate_only: true,
    }
    if (searchQuery.value.trim()) {
      params.search_query = searchQuery.value.trim()
    }
    const [listRes, countRes] = await Promise.all([
      transactionStore.fetchTransactions(params),
    ])
    duplicates.value = transactionStore.transactions
    totalCount.value = transactionStore.totalCount
  } finally {
    loading.value = false
  }
}

async function loadOriginal(txId, originalId) {
  if (originals.value[txId]) return
  try {
    const data = await transactionStore.fetchTransaction(originalId)
    originals.value[txId] = data
  } catch {
    // ignore
  }
}

function onRowExpand(event) {
  const tx = event.data
  if (tx.id_duplicate_of) {
    loadOriginal(tx.id, tx.id_duplicate_of)
  }
}

async function unmark(id) {
  try {
    await transactionStore.unmarkDuplicate(id)
    toast.add({ severity: 'success', summary: t('settings.duplicates'), detail: t('settings.unmarkDuplicate'), life: 2000 })
    await loadDuplicates()
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.duplicates'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

function onPage(event) {
  page.value = event.page
  pageSize.value = event.rows
  loadDuplicates()
}

let debounceTimer = null
function debouncedSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 0
    loadDuplicates()
  }, 300)
}

onMounted(() => loadDuplicates())
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold">{{ t('settings.duplicateManagement') }}</h3>
      <InputText
        v-model="searchQuery"
        :placeholder="t('common.search')"
        size="small"
        class="w-60"
        @input="debouncedSearch"
      />
    </div>

    <div v-if="!loading && duplicates.length === 0" class="text-center py-8 text-surface-400">
      <i class="pi pi-check-circle text-3xl mb-2 block"></i>
      <p>{{ t('settings.noDuplicates') }}</p>
    </div>

    <div v-else class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        v-model:expandedRows="expandedRows"
        :value="duplicates"
        :loading="loading"
        :lazy="true"
        :paginator="true"
        :rows="pageSize"
        :totalRecords="totalCount"
        @page="onPage"
        @row-expand="onRowExpand"
        dataKey="id"
        stripedRows
        class="text-sm"
      >
        <Column expander style="width: 3rem" />
        <Column field="date" :header="t('transactions.date')" style="width: 110px" />
        <Column field="description" :header="t('transactions.description')" />
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
        <Column :header="t('transactions.source')" style="width: 150px">
          <template #body="{ data }">
            <AccountDisplay :account="data.source" />
          </template>
        </Column>
        <Column style="width: 120px">
          <template #body="{ data }">
            <Button
              :label="t('settings.unmarkDuplicate')"
              severity="secondary"
              text
              size="small"
              @click="unmark(data.id)"
            />
          </template>
        </Column>

        <template #expansion="{ data }">
          <div class="p-4">
            <div v-if="originals[data.id]" class="grid grid-cols-2 gap-4">
              <div>
                <div class="text-xs font-semibold text-surface-500 mb-2">{{ t('settings.duplicate') }}</div>
                <div class="bg-red-50 rounded-lg p-3 text-sm space-y-1">
                  <div><strong>{{ t('transactions.date') }}:</strong> {{ data.date }}</div>
                  <div><strong>{{ t('transactions.description') }}:</strong> {{ data.description || '—' }}</div>
                  <div><strong>{{ t('transactions.amount') }}:</strong> {{ data.amount }} {{ data.currency?.symbol }}</div>
                  <div class="flex items-start gap-2"><strong>{{ t('transactions.source') }}:</strong> <AccountDisplay :account="data.source" /></div>
                  <div class="flex items-start gap-2"><strong>{{ t('transactions.dest') }}:</strong> <AccountDisplay :account="data.dest" /></div>
                  <div><strong>ID:</strong> {{ data.external_id || '—' }}</div>
                </div>
              </div>
              <div>
                <div class="text-xs font-semibold text-surface-500 mb-2">{{ t('settings.original') }}</div>
                <div class="bg-green-50 rounded-lg p-3 text-sm space-y-1">
                  <div><strong>{{ t('transactions.date') }}:</strong> {{ originals[data.id].date }}</div>
                  <div><strong>{{ t('transactions.description') }}:</strong> {{ originals[data.id].description || '—' }}</div>
                  <div><strong>{{ t('transactions.amount') }}:</strong> {{ originals[data.id].amount }} {{ originals[data.id].currency?.symbol }}</div>
                  <div class="flex items-start gap-2"><strong>{{ t('transactions.source') }}:</strong> <AccountDisplay :account="originals[data.id].source" /></div>
                  <div class="flex items-start gap-2"><strong>{{ t('transactions.dest') }}:</strong> <AccountDisplay :account="originals[data.id].dest" /></div>
                  <div><strong>ID:</strong> {{ originals[data.id].external_id || '—' }}</div>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-surface-400 py-4">
              <i class="pi pi-spinner pi-spin"></i>
            </div>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>
