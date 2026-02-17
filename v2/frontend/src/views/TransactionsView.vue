<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../stores/transactions'
import { useCategoryStore } from '../stores/categories'
import { useTransactionGroupStore } from '../stores/transactionGroups'
import TransactionGroupDialog from '../components/transactions/TransactionGroupDialog.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Button from 'primevue/button'

const { t } = useI18n()
const transactionStore = useTransactionStore()
const categoryStore = useCategoryStore()
const groupStore = useTransactionGroupStore()

const groupDialogVisible = ref(false)
const groupDialogGroup = ref(null)
const groupDialogInitialTx = ref(null)

function openGroupDialog(tx) {
  if (tx.id_transaction_group) {
    groupStore.fetchGroup(tx.id_transaction_group).then((g) => {
      groupDialogGroup.value = g
      groupDialogInitialTx.value = null
      groupDialogVisible.value = true
    })
  } else {
    groupDialogGroup.value = null
    groupDialogInitialTx.value = tx
    groupDialogVisible.value = true
  }
}

function onGroupSaved() {
  loadData()
}

const page = ref(0)
const pageSize = ref(50)
const searchQuery = ref('')
const labeledFilter = ref(null)
const sortField = ref('date')
const sortOrder = ref(-1)

const labeledOptions = [
  { label: 'All', value: null },
  { label: 'Labeled', value: true },
  { label: 'Unlabeled', value: false },
]

async function loadData() {
  const params = {
    start: page.value * pageSize.value,
    count: pageSize.value,
    sort_by: sortField.value === 'date' ? 'when' : sortField.value,
    order: sortOrder.value === 1 ? 'asc' : 'desc',
  }
  if (searchQuery.value.length >= 3) params.search_query = searchQuery.value
  if (labeledFilter.value !== null) params.labeled = labeledFilter.value

  await transactionStore.fetchTransactions(params)
}

function onPage(event) {
  page.value = event.page
  pageSize.value = event.rows
  loadData()
}

function onSort(event) {
  sortField.value = event.sortField
  sortOrder.value = event.sortOrder
  loadData()
}

let searchTimeout = null
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 0
    loadData()
  }, 400)
})

watch(labeledFilter, () => {
  page.value = 0
  loadData()
})

onMounted(async () => {
  await Promise.all([loadData(), categoryStore.fetchCategories()])
})

async function onCategoryChange(transactionId, categoryId) {
  await transactionStore.setCategory(transactionId, categoryId)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">{{ t('transactions.title') }}</h1>

    <div class="flex flex-wrap gap-3 mb-4">
      <InputText
        v-model="searchQuery"
        :placeholder="t('common.search')"
        class="w-full md:w-64"
      />
      <Select
        v-model="labeledFilter"
        :options="labeledOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Filter"
        class="w-full md:w-40"
      />
    </div>

    <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        :value="transactionStore.transactions"
        :loading="transactionStore.loading"
        :lazy="true"
        :paginator="true"
        :rows="pageSize"
        :totalRecords="transactionStore.totalCount"
        :sortField="sortField"
        :sortOrder="sortOrder"
        @page="onPage"
        @sort="onSort"
        stripedRows
        responsiveLayout="scroll"
        class="text-sm"
      >
        <Column field="date" :header="t('transactions.date')" sortable style="width: 110px" />

        <Column field="description" :header="t('transactions.description')">
          <template #body="{ data }">
            <span class="truncate block max-w-xs">{{ data.description || '—' }}</span>
          </template>
        </Column>

        <Column field="source" :header="t('transactions.source')" style="width: 150px">
          <template #body="{ data }">
            {{ data.source?.name || data.source?.number || '—' }}
          </template>
        </Column>

        <Column field="dest" :header="t('transactions.dest')" style="width: 150px">
          <template #body="{ data }">
            {{ data.dest?.name || data.dest?.number || '—' }}
          </template>
        </Column>

        <Column field="amount" :header="t('transactions.amount')" sortable style="width: 120px">
          <template #body="{ data }">
            <span :class="data.id_source ? 'text-red-500' : 'text-green-600'" class="font-medium">
              {{ data.id_source ? '-' : '+' }}{{ data.amount }}
            </span>
            <span
              v-if="data.effective_amount != null && data.effective_amount !== data.amount"
              class="text-xs text-surface-400 block"
            >
              ({{ t('transactions.effectiveAmount') }}: {{ data.effective_amount }})
            </span>
          </template>
        </Column>

        <Column :header="t('transactions.group')" style="width: 100px">
          <template #body="{ data }">
            <Button
              v-if="data.id_transaction_group"
              :label="t('transactions.group')"
              severity="info"
              text
              size="small"
              @click="openGroupDialog(data)"
            />
            <Button
              v-else
              icon="pi pi-link"
              severity="secondary"
              text
              size="small"
              @click="openGroupDialog(data)"
              :aria-label="t('transactions.createGroup')"
            />
          </template>
        </Column>

        <Column field="category" :header="t('transactions.category')" style="width: 180px">
          <template #body="{ data }">
            <Select
              :modelValue="data.id_category"
              @update:modelValue="(v) => onCategoryChange(data.id, v)"
              :options="categoryStore.categories"
              optionLabel="name"
              optionValue="id"
              :placeholder="t('transactions.uncategorized')"
              class="w-full text-xs"
              :showClear="true"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <TransactionGroupDialog
      v-model:visible="groupDialogVisible"
      :group="groupDialogGroup"
      :initialTransaction="groupDialogInitialTx"
      @saved="onGroupSaved"
      @deleted="onGroupSaved"
    />
  </div>
</template>
