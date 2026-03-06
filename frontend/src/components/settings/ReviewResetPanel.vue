<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useTransactionStore } from '../../stores/transactions'
import Card from 'primevue/card'
import Button from 'primevue/button'

const { t } = useI18n()
const toast = useToast()
const transactionStore = useTransactionStore()
const loading = ref(false)

async function unreviewUncategorized() {
  loading.value = true
  try {
    const result = await transactionStore.unreviewUncategorized()
    await transactionStore.fetchReviewCount()
    toast.add({
      severity: 'success',
      summary: t('settings.unreviewUncategorized'),
      detail: t('settings.unreviewResult', { transactions: result.transactions, groups: result.groups }),
      life: 5000,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('settings.unreviewUncategorized'), detail: 'Failed', life: 3000 })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Card>
    <template #title>{{ t('settings.unreviewUncategorized') }}</template>
    <template #content>
      <p class="text-sm text-surface-600 mb-4">{{ t('settings.unreviewUncategorizedDesc') }}</p>
      <Button
        :label="t('settings.unreviewUncategorizedBtn')"
        icon="pi pi-replay"
        severity="warn"
        :loading="loading"
        @click="unreviewUncategorized"
      />
    </template>
  </Card>
</template>
