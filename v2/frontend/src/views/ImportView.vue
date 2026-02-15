<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import api from '../services/api'
import FileUpload from 'primevue/fileupload'
import Select from 'primevue/select'
import Button from 'primevue/button'

const { t } = useI18n()
const toast = useToast()

const format = ref('belfius')
const uploading = ref(false)
const result = ref(null)

const formatOptions = [
  { label: 'Belfius CSV', value: 'belfius' },
  { label: 'ING CSV', value: 'ing' },
  { label: 'MasterCard PDF', value: 'mastercard_pdf' },
]

async function onUpload(event) {
  uploading.value = true
  result.value = null

  const formData = new FormData()
  for (const file of event.files) {
    formData.append('files', file)
  }

  try {
    const { data } = await api.post(`/imports/upload?format=${format.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
    toast.add({ severity: 'success', summary: 'Import complete', detail: `${data.imported} transactions imported`, life: 5000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Import failed', detail: err.response?.data?.detail || 'Error', life: 5000 })
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">{{ t('nav.import') }}</h1>

    <div class="bg-surface-0 rounded-xl shadow p-6 max-w-xl">
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
          :chooseLabel="'Choose files'"
          :uploadLabel="uploading ? 'Uploading...' : 'Upload'"
          :disabled="uploading"
          accept=".csv,.pdf"
        />

        <div v-if="result" class="mt-2 p-3 bg-green-50 text-green-800 rounded-lg text-sm">
          Imported {{ result.imported }} transaction(s).
        </div>
      </div>
    </div>
  </div>
</template>
