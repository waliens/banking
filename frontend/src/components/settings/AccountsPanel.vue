<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccountStore } from '../../stores/accounts'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const { t } = useI18n()
const toast = useToast()
const accountStore = useAccountStore()

const rows = ref(20)
const first = ref(0)
const expandedRows = ref([])

// Inline editing
const editingAccountId = ref(null)
const editForm = ref({ name: '', number: '' })

// Add alias form
const addingAliasForId = ref(null)
const newAlias = ref({ name: '', number: '' })

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

function startEditing(account) {
  editingAccountId.value = account.id
  editForm.value = { name: account.name || '', number: account.number || '' }
}

function cancelEditing() {
  editingAccountId.value = null
}

async function saveEditing(account) {
  try {
    await accountStore.updateAccount(account.id, editForm.value)
    editingAccountId.value = null
    toast.add({ severity: 'success', summary: t('accounts.title'), detail: 'Updated', life: 2000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: t('accounts.title'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

async function removeAlias(accountId, aliasId) {
  try {
    await accountStore.removeAlias(accountId, aliasId)
    await loadPage()
    toast.add({ severity: 'success', summary: t('settings.accounts'), detail: t('settings.aliasRemoved'), life: 2000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.accounts'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

function startAddAlias(accountId) {
  addingAliasForId.value = accountId
  newAlias.value = { name: '', number: '' }
}

async function saveNewAlias(accountId) {
  try {
    await accountStore.addAlias(accountId, newAlias.value)
    addingAliasForId.value = null
    await loadPage()
    toast.add({ severity: 'success', summary: t('settings.accounts'), detail: t('settings.aliasAdded'), life: 2000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.accounts'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

onMounted(async () => {
  await Promise.all([accountStore.fetchCount(), loadPage()])
})
</script>

<template>
  <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
    <DataTable
      v-model:expandedRows="expandedRows"
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
      dataKey="id"
      class="text-sm"
    >
      <Column expander style="width: 3rem" />

      <Column field="name" header="Name">
        <template #body="{ data }">
          <template v-if="editingAccountId === data.id">
            <InputText v-model="editForm.name" size="small" class="w-full" />
          </template>
          <template v-else>
            {{ data.name || '—' }}
          </template>
        </template>
      </Column>
      <Column field="number" header="Number">
        <template #body="{ data }">
          <template v-if="editingAccountId === data.id">
            <InputText v-model="editForm.number" size="small" class="w-full" />
          </template>
          <template v-else>
            <code class="text-xs">{{ data.number || '—' }}</code>
          </template>
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
      <Column style="width: 100px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <template v-if="editingAccountId === data.id">
              <Button icon="pi pi-check" text rounded size="small" @click="saveEditing(data)" />
              <Button icon="pi pi-times" text rounded size="small" severity="secondary" @click="cancelEditing" />
            </template>
            <template v-else>
              <Button icon="pi pi-pencil" text rounded size="small" @click="startEditing(data)" />
            </template>
          </div>
        </template>
      </Column>

      <template #expansion="{ data }">
        <div class="p-3">
          <div class="text-xs font-semibold text-surface-500 mb-2">{{ t('settings.aliases') }} ({{ data.aliases?.length || 0 }})</div>
          <div v-if="data.aliases?.length" class="space-y-1 mb-3">
            <div
              v-for="alias in data.aliases"
              :key="alias.id"
              class="flex items-center justify-between bg-surface-50 rounded px-3 py-1.5 text-sm"
            >
              <div>
                <span>{{ alias.name || '—' }}</span>
                <code v-if="alias.number" class="text-xs ml-2 text-surface-400">{{ alias.number }}</code>
              </div>
              <Button
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                @click="removeAlias(data.id, alias.id)"
              />
            </div>
          </div>
          <div v-else class="text-xs text-surface-400 mb-3">{{ t('settings.noAliases') }}</div>

          <!-- Add alias form -->
          <div v-if="addingAliasForId === data.id" class="flex items-end gap-2">
            <div class="flex flex-col gap-1">
              <label class="text-xs text-surface-500">{{ t('settings.aliasName') }}</label>
              <InputText v-model="newAlias.name" size="small" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-xs text-surface-500">{{ t('settings.aliasNumber') }}</label>
              <InputText v-model="newAlias.number" size="small" />
            </div>
            <Button icon="pi pi-check" size="small" @click="saveNewAlias(data.id)" />
            <Button icon="pi pi-times" size="small" severity="secondary" text @click="addingAliasForId = null" />
          </div>
          <Button
            v-else
            :label="t('settings.addAlias')"
            icon="pi pi-plus"
            text
            size="small"
            @click="startAddAlias(data.id)"
          />
        </div>
      </template>
    </DataTable>
  </div>
</template>
