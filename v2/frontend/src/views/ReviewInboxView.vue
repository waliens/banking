<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../stores/transactions'
import { useCategoryStore } from '../stores/categories'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DuplicateCandidates from '../components/transactions/DuplicateCandidates.vue'

const { t } = useI18n()
const transactionStore = useTransactionStore()
const categoryStore = useCategoryStore()

const page = ref(0)
const pageSize = ref(50)
const expandedRows = ref([])

const inboxParams = {
  is_reviewed: false,
  labeled: false,
  duplicate_only: false,
}

async function loadData() {
  await transactionStore.fetchTransactions({
    ...inboxParams,
    start: page.value * pageSize.value,
    count: pageSize.value,
    order: 'desc',
  })
}

function onPage(event) {
  page.value = event.page
  pageSize.value = event.rows
  loadData()
}

async function onCategoryChange(transactionId, categoryId) {
  await transactionStore.setCategory(transactionId, categoryId)
  await refreshAfterAction()
}

async function markReviewed(id) {
  await transactionStore.reviewTransaction(id)
  await refreshAfterAction()
}

async function markAllReviewed() {
  const ids = transactionStore.transactions.map((t) => t.id)
  if (ids.length === 0) return
  await transactionStore.reviewBatch(ids)
  await refreshAfterAction()
}

async function refreshAfterAction() {
  await Promise.all([loadData(), transactionStore.fetchReviewCount()])
}

function onDuplicateResolved() {
  refreshAfterAction()
}

onMounted(async () => {
  await Promise.all([loadData(), categoryStore.fetchCategories(), transactionStore.fetchReviewCount()])
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
      <Button
        :label="t('review.markAllReviewed')"
        severity="secondary"
        size="small"
        icon="pi pi-check-circle"
        :disabled="transactionStore.transactions.length === 0"
        @click="markAllReviewed"
      />
    </div>

    <div v-if="!transactionStore.loading && transactionStore.transactions.length === 0" class="text-center py-12 text-surface-400">
      <i class="pi pi-check-circle text-4xl mb-3 block" />
      <p>{{ t('review.empty') }}</p>
    </div>

    <div v-else class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        v-model:expandedRows="expandedRows"
        :value="transactionStore.transactions"
        :loading="transactionStore.loading"
        :lazy="true"
        :paginator="true"
        :rows="pageSize"
        :totalRecords="transactionStore.totalCount"
        @page="onPage"
        dataKey="id"
        stripedRows
        responsiveLayout="scroll"
        class="text-sm"
      >
        <Column expander style="width: 3rem" />

        <Column field="date" :header="t('transactions.date')" style="width: 110px" />

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

        <Column field="amount" :header="t('transactions.amount')" style="width: 120px">
          <template #body="{ data }">
            <span :class="data.id_source ? 'text-red-500' : 'text-green-600'" class="font-medium">
              {{ data.id_source ? '-' : '+' }}{{ data.amount }}
            </span>
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
            />
          </template>
        </Column>

        <Column style="width: 120px">
          <template #body="{ data }">
            <Button
              :label="t('review.markReviewed')"
              severity="secondary"
              size="small"
              text
              @click="markReviewed(data.id)"
            />
          </template>
        </Column>

        <template #expansion="{ data }">
          <DuplicateCandidates :transactionId="data.id" @resolved="onDuplicateResolved" />
        </template>
      </DataTable>
    </div>
  </div>
</template>
