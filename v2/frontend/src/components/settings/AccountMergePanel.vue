<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccountStore } from '../../stores/accounts'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import AccountSelect from '../common/AccountSelect.vue'
import AccountDisplay from '../common/AccountDisplay.vue'

const { t } = useI18n()
const toast = useToast()
const accountStore = useAccountStore()

const idRepr = ref(null)
const idAlias = ref(null)
const merging = ref(false)
const dismissedSuggestions = ref(new Set())

const canMerge = computed(() =>
  idRepr.value != null && idAlias.value != null && idRepr.value !== idAlias.value,
)

const visibleSuggestions = computed(() =>
  accountStore.mergeSuggestions.filter(
    (s) => !dismissedSuggestions.value.has(`${s.account_a.id}-${s.account_b.id}`),
  ),
)

function reasonLabel(reason) {
  const labels = {
    similar_name: t('settings.similarName'),
    same_bank: t('settings.sameBank'),
    same_number: t('settings.sameNumber'),
    same_name_different_number: t('settings.sameNameDiffNumber'),
  }
  return labels[reason] || reason
}

function dismissSuggestion(suggestion) {
  dismissedSuggestions.value.add(`${suggestion.account_a.id}-${suggestion.account_b.id}`)
}

async function acceptSuggestion(suggestion) {
  if (!confirm(t('settings.mergeWarning'))) return
  merging.value = true
  try {
    await accountStore.mergeAccounts(suggestion.account_a.id, suggestion.account_b.id)
    toast.add({ severity: 'success', summary: t('settings.mergeAccounts'), detail: 'OK', life: 3000 })
    await Promise.all([accountStore.fetchAccounts(), accountStore.fetchMergeSuggestions()])
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.mergeAccounts'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  } finally {
    merging.value = false
  }
}

async function merge() {
  if (!canMerge.value) return
  if (!confirm(t('settings.mergeWarning'))) return

  merging.value = true
  try {
    await accountStore.mergeAccounts(idRepr.value, idAlias.value)
    toast.add({ severity: 'success', summary: t('settings.mergeAccounts'), detail: 'OK', life: 3000 })
    idRepr.value = null
    idAlias.value = null
    await Promise.all([accountStore.fetchAccounts(), accountStore.fetchMergeSuggestions()])
  } catch (err) {
    toast.add({ severity: 'error', summary: t('settings.mergeAccounts'), detail: err.response?.data?.detail || 'Failed', life: 3000 })
  } finally {
    merging.value = false
  }
}

onMounted(() => {
  accountStore.fetchMergeSuggestions()
})
</script>

<template>
  <div class="pb-6">
    <!-- Suggested Merges -->
    <div v-if="visibleSuggestions.length > 0" class="mb-6">
      <h3 class="text-base font-semibold mb-3">{{ t('settings.suggestedMerges') }}</h3>
      <div class="space-y-2">
        <div
          v-for="suggestion in visibleSuggestions"
          :key="`${suggestion.account_a.id}-${suggestion.account_b.id}`"
          class="bg-surface-0 rounded-lg shadow-sm p-3 flex items-center justify-between gap-3"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <AccountDisplay :account="suggestion.account_a" class="text-sm min-w-0" />
            <i class="pi pi-arrow-right-arrow-left text-surface-400 text-xs shrink-0"></i>
            <AccountDisplay :account="suggestion.account_b" class="text-sm min-w-0" />
            <Tag :value="reasonLabel(suggestion.reason)" severity="info" class="text-xs shrink-0" />
          </div>
          <div class="flex gap-1 shrink-0">
            <Button
              :label="t('settings.mergeButton')"
              icon="pi pi-check"
              severity="primary"
              size="small"
              :loading="merging"
              @click="acceptSuggestion(suggestion)"
            />
            <Button
              :label="t('review.dismiss')"
              icon="pi pi-times"
              severity="secondary"
              text
              size="small"
              @click="dismissSuggestion(suggestion)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Manual Merge -->
    <h3 class="text-base font-semibold mb-3">{{ t('settings.mergeAccounts') }}</h3>
    <p class="text-sm text-surface-500 mb-4">{{ t('settings.mergeWarning') }}</p>
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-500">{{ t('settings.mergeRepresentative') }}</label>
        <AccountSelect v-model="idRepr" placeholder="Select account" class="w-60" />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-500">{{ t('settings.mergeAlias') }}</label>
        <AccountSelect v-model="idAlias" placeholder="Select account" class="w-60" />
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
