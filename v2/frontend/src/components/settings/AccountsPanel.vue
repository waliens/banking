<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccountStore } from '../../stores/accounts'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'

const { t } = useI18n()
const accountStore = useAccountStore()

const rows = ref(20)
const first = ref(0)

async function loadPage() {
  await accountStore.fetchAccounts({ start: first.value, count: rows.value })
}

function onPage(event) {
  first.value = event.first
  rows.value = event.rows
  loadPage()
}

async function toggleActive(account) {
  await accountStore.updateAccount(account.id, { is_active: !account.is_active })
}

onMounted(async () => {
  await Promise.all([accountStore.fetchCount(), loadPage()])
})
</script>

<template>
  <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
    <DataTable
      :value="accountStore.accounts"
      :loading="accountStore.loading"
      lazy
      paginator
      :rows="rows"
      :totalRecords="accountStore.totalCount"
      :first="first"
      :rowsPerPageOptions="[10, 20, 50]"
      @page="onPage"
      stripedRows
      responsiveLayout="scroll"
      class="text-sm"
    >
      <Column field="name" header="Name">
        <template #body="{ data }">
          {{ data.name || '—' }}
        </template>
      </Column>
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
      <Column field="initial_balance" :header="t('accounts.initialBalance')">
        <template #body="{ data }">
          {{ data.initial_balance }} {{ data.currency?.symbol }}
        </template>
      </Column>
      <Column :header="t('settings.active')" style="width: 80px">
        <template #body="{ data }">
          <ToggleSwitch :modelValue="data.is_active" @update:modelValue="toggleActive(data)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
