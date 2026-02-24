<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useImportStore } from '../stores/imports'
import api from '../services/api'
import FileUpload from 'primevue/fileupload'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const importStore = useImportStore()

const format = ref('belfius')
const uploading = ref(false)
const lastImportId = ref(null)

const formatOptions = [
  { label: 'Belfius CSV', value: 'belfius' },
  { label: 'ING CSV', value: 'ing' },
  { label: 'MasterCard PDF', value: 'mastercard_pdf' },
]

async function onUpload(event) {
  uploading.value = true
  lastImportId.value = null

  const formData = new FormData()
  for (const file of event.files) {
    formData.append('files', file)
  }

  try {
    const { data } = await api.post(`/imports/upload?format=${format.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    lastImportId.value = data.id
    toast.add({
      severity: 'success',
      summary: t('import.complete'),
      detail: `${data.new_transactions} ${t('import.newTransactions')}, ${data.duplicate_transactions} ${t('import.duplicates')}`,
      life: 5000,
    })
    await importStore.fetchImports()
  } catch (err) {
    toast.add({ severity: 'error', summary: t('import.failed'), detail: err.response?.data?.detail || 'Error', life: 5000 })
  } finally {
    uploading.value = false
  }
}

function goToImportDetail(id) {
  router.push(`/imports/${id}`)
}

function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString()
}

onMounted(() => {
  importStore.fetchImports()
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">{{ t('nav.import') }}</h1>

    <!-- Upload section -->
    <div class="bg-surface-0 rounded-xl shadow p-6 w-full mb-6">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Format</label>
          <Select v-model="format" :options="formatOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>

        <FileUpload
          mode="advanced"
          :multiple="true"
          :auto="false"
          :customUpload="true"
          @uploader="onUpload"
          :chooseLabel="t('import.chooseFiles')"
          :uploadLabel="uploading ? t('import.uploading') : t('import.upload')"
          :disabled="uploading"
          accept=".csv,.pdf"
        />

        <div v-if="lastImportId" class="mt-2 p-3 bg-green-50 text-green-800 rounded-lg text-sm flex items-center justify-between">
          <span>{{ t('import.importSuccess') }}</span>
          <Button :label="t('import.viewDetails')" text size="small" @click="goToImportDetail(lastImportId)" />
        </div>
      </div>
    </div>

    <!-- Import History -->
    <h2 class="text-lg font-semibold mb-3">{{ t('import.history') }}</h2>
    <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable
        :value="importStore.imports"
        :loading="importStore.loading"
        stripedRows
        class="text-sm cursor-pointer"
        @row-click="(e) => goToImportDetail(e.data.id)"
      >
        <Column :header="t('import.dateTime')" style="width: 180px">
          <template #body="{ data }">
            {{ formatDateTime(data.created_at) }}
          </template>
        </Column>
        <Column field="format" :header="t('import.format')" style="width: 120px">
          <template #body="{ data }">
            <Tag :value="data.format" />
          </template>
        </Column>
        <Column :header="t('import.files')" style="width: 80px">
          <template #body="{ data }">
            {{ data.filenames?.length || 0 }}
          </template>
        </Column>
        <Column :header="t('import.newTransactions')" style="width: 100px">
          <template #body="{ data }">
            {{ data.new_transactions }}
          </template>
        </Column>
        <Column :header="t('import.duplicates')" style="width: 100px">
          <template #body="{ data }">
            {{ data.duplicate_transactions }}
          </template>
        </Column>
        <Column :header="t('import.skipped')" style="width: 100px">
          <template #body="{ data }">
            {{ data.skipped_transactions }}
          </template>
        </Column>
        <Column :header="t('import.autoTagged')" style="width: 100px">
          <template #body="{ data }">
            {{ data.auto_tagged }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
