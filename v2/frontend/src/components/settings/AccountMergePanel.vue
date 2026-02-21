<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccountStore } from '../../stores/accounts'
import { useToast } from 'primevue/usetoast'
import Select from 'primevue/select'
import Button from 'primevue/button'

const { t } = useI18n()
const toast = useToast()
const accountStore = useAccountStore()

const idRepr = ref(null)
const idAlias = ref(null)
const merging = ref(false)

const canMerge = computed(() =>
  idRepr.value != null && idAlias.value != null && idRepr.value !== idAlias.value,
)

async function merge() {
  if (!canMerge.value) return
  if (!confirm(t('settings.mergeWarning'))) return

  merging.value = true
  try {
    await accountStore.mergeAccounts(idRepr.value, idAlias.value)
    toast.add({ severity: 'success', summary: t('settings.mergeAccounts'), detail: 'OK', life: 3000 })
    idRepr.value = null
    idAlias.value = null
    await accountStore.fetchAccounts()
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.mergeAccounts'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  } finally {
    merging.value = false
  }
}
</script>

<template>
  <div class="pb-6">
    <h3 class="text-base font-semibold mb-3">{{ t('settings.mergeAccounts') }}</h3>
    <p class="text-sm text-surface-500 mb-4">{{ t('settings.mergeWarning') }}</p>
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-500">{{ t('settings.mergeRepresentative') }}</label>
        <Select
          v-model="idRepr"
          :options="accountStore.accounts"
          optionLabel="name"
          optionValue="id"
          placeholder="Select account"
          class="w-60"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-500">{{ t('settings.mergeAlias') }}</label>
        <Select
          v-model="idAlias"
          :options="accountStore.accounts"
          optionLabel="name"
          optionValue="id"
          placeholder="Select account"
          class="w-60"
        />
      </div>
      <Button
        :label="t('settings.mergeButton')"
        icon="pi pi-arrow-right-arrow-left"
        severity="danger"
        :disabled="!canMerge"
        :loading="merging"
        @click="merge"
      />
    </div>
    <div class="mt-6 pt-4 border-t border-surface-200"></div>
  </div>
</template>
