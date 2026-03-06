<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useMLStore } from '../../stores/ml'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

const { t } = useI18n()
const toast = useToast()
const mlStore = useMLStore()

const training = ref(false)

const stateSeverity = {
  ready: 'success',
  training: 'warn',
  failed: 'danger',
}

async function trainNow() {
  training.value = true
  try {
    await mlStore.trainModel()
    toast.add({ severity: 'success', summary: t('ml.train'), detail: t('settings.trainStarted'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('ml.train'), detail: t('settings.trainFailed'), life: 3000 })
  } finally {
    training.value = false
  }
}

onMounted(() => mlStore.fetchModels())
</script>

<template>
  <div>
    <div class="flex justify-end mb-4">
      <Button :label="t('settings.trainNow')" icon="pi pi-cog" size="small" :loading="training" @click="trainNow" />
    </div>

    <div v-if="mlStore.models.length === 0" class="text-center text-surface-500 py-8">
      {{ t('settings.noModels') }}
    </div>

    <div v-else class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable :value="mlStore.models" stripedRows class="text-sm">
        <Column field="filename" :header="t('settings.filename')" />
        <Column field="state" :header="t('settings.status')">
          <template #body="{ data }">
            <Tag :value="data.state" :severity="stateSeverity[data.state] || 'info'" />
          </template>
        </Column>
        <Column field="cv_score" :header="t('settings.score')">
          <template #body="{ data }">
            {{ data.cv_score != null ? (data.cv_score * 100).toFixed(1) + '%' : '—' }}
          </template>
        </Column>
        <Column field="n_samples" :header="t('settings.samples')" />
        <Column field="created_at" :header="t('transactions.date')">
          <template #body="{ data }">
            {{ data.created_at ? new Date(data.created_at).toLocaleDateString() : '—' }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
