<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '../stores/auth'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Password from 'primevue/password'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import AccountsPanel from '../components/settings/AccountsPanel.vue'
import CategoriesPanel from '../components/settings/CategoriesPanel.vue'
import TagRulesPanel from '../components/settings/TagRulesPanel.vue'
import MLModelsPanel from '../components/settings/MLModelsPanel.vue'

const { t } = useI18n()
const toast = useToast()
const authStore = useAuthStore()

const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)

async function savePassword() {
  if (newPassword.value !== confirmPassword.value) {
    toast.add({ severity: 'warn', summary: t('settings.changePassword'), detail: t('settings.passwordMismatch'), life: 3000 })
    return
  }
  if (!newPassword.value) return

  saving.value = true
  try {
    await authStore.changePassword(newPassword.value)
    toast.add({ severity: 'success', summary: t('settings.changePassword'), detail: t('settings.passwordChanged'), life: 3000 })
    newPassword.value = ''
    confirmPassword.value = ''
  } catch {
    toast.add({ severity: 'error', summary: t('settings.changePassword'), detail: 'Failed', life: 3000 })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">{{ t('settings.title') }}</h1>

    <Card class="mb-6">
      <template #title>{{ t('settings.changePassword') }}</template>
      <template #content>
        <div class="flex flex-col gap-4 max-w-sm">
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('settings.newPassword') }}</label>
            <Password v-model="newPassword" :feedback="false" toggleMask class="w-full" inputClass="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('settings.confirmPassword') }}</label>
            <Password v-model="confirmPassword" :feedback="false" toggleMask class="w-full" inputClass="w-full" />
          </div>
          <div>
            <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="savePassword" />
          </div>
        </div>
      </template>
    </Card>

    <Tabs value="accounts">
      <TabList>
        <Tab value="accounts">{{ t('settings.accounts') }}</Tab>
        <Tab value="categories">{{ t('settings.categories') }}</Tab>
        <Tab value="rules">{{ t('settings.rules') }}</Tab>
        <Tab value="ml">{{ t('settings.mlModels') }}</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="accounts">
          <AccountsPanel />
        </TabPanel>
        <TabPanel value="categories">
          <CategoriesPanel />
        </TabPanel>
        <TabPanel value="rules">
          <TagRulesPanel />
        </TabPanel>
        <TabPanel value="ml">
          <MLModelsPanel />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>
