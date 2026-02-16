<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useTagRuleStore } from '../../stores/tagRules'
import { useCategoryStore } from '../../stores/categories'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'

const { t } = useI18n()
const toast = useToast()
const tagRuleStore = useTagRuleStore()
const categoryStore = useCategoryStore()

const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({
  name: '',
  id_category: null,
  match_description: null,
  match_amount_min: null,
  match_amount_max: null,
  priority: 0,
  is_active: true,
})

function openCreate() {
  editing.value = null
  form.value = { name: '', id_category: null, match_description: null, match_amount_min: null, match_amount_max: null, priority: 0, is_active: true }
  dialogVisible.value = true
}

function openEdit(rule) {
  editing.value = rule.id
  form.value = {
    name: rule.name,
    id_category: rule.id_category,
    match_description: rule.match_description,
    match_amount_min: rule.match_amount_min ? Number(rule.match_amount_min) : null,
    match_amount_max: rule.match_amount_max ? Number(rule.match_amount_max) : null,
    priority: rule.priority,
    is_active: rule.is_active,
  }
  dialogVisible.value = true
}

async function saveRule() {
  const payload = { ...form.value }
  if (editing.value) {
    await tagRuleStore.updateRule(editing.value, payload)
  } else {
    await tagRuleStore.createRule(payload)
  }
  dialogVisible.value = false
}

async function deleteRule(id) {
  await tagRuleStore.deleteRule(id)
}

async function toggleActive(rule) {
  await tagRuleStore.updateRule(rule.id, { is_active: !rule.is_active })
}

async function applyAll() {
  const count = await tagRuleStore.applyRules()
  toast.add({
    severity: 'success',
    summary: t('rules.applied'),
    detail: `${count} ${t('transactions.title').toLowerCase()}`,
    life: 3000,
  })
}

onMounted(async () => {
  await Promise.all([tagRuleStore.fetchRules(), categoryStore.fetchCategories()])
})
</script>

<template>
  <div>
    <div class="flex justify-end mb-4 gap-2">
      <Button :label="t('rules.apply')" severity="secondary" icon="pi pi-play" size="small" @click="applyAll" />
      <Button :label="t('common.create')" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <div class="bg-surface-0 rounded-xl shadow overflow-hidden">
      <DataTable :value="tagRuleStore.rules" :loading="tagRuleStore.loading" stripedRows class="text-sm">
        <Column field="name" :header="t('rules.name')" />

        <Column field="category" :header="t('transactions.category')">
          <template #body="{ data }">
            <span
              v-if="data.category"
              class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
              :style="{ backgroundColor: data.category.color + '20', color: data.category.color }"
            >
              {{ data.category.name }}
            </span>
          </template>
        </Column>

        <Column field="match_description" :header="t('rules.pattern')" />

        <Column :header="t('rules.amountRange')">
          <template #body="{ data }">
            <span v-if="data.match_amount_min || data.match_amount_max">
              {{ data.match_amount_min ?? '...' }} - {{ data.match_amount_max ?? '...' }}
            </span>
            <span v-else class="text-surface-400">-</span>
          </template>
        </Column>

        <Column field="priority" :header="t('rules.priority')" style="width: 100px" />

        <Column :header="t('rules.active')" style="width: 80px">
          <template #body="{ data }">
            <ToggleSwitch :modelValue="data.is_active" @update:modelValue="toggleActive(data)" />
          </template>
        </Column>

        <Column style="width: 100px">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button icon="pi pi-pencil" severity="secondary" text size="small" @click="openEdit(data)" />
              <Button icon="pi pi-trash" severity="danger" text size="small" @click="deleteRule(data.id)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="dialogVisible" :header="editing ? t('common.edit') : t('common.create')" modal class="w-full max-w-lg">
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('rules.name') }}</label>
          <InputText v-model="form.name" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">{{ t('transactions.category') }}</label>
          <Select
            v-model="form.id_category"
            :options="categoryStore.categories"
            optionLabel="name"
            optionValue="id"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">{{ t('rules.pattern') }}</label>
          <InputText v-model="form.match_description" class="w-full" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('rules.amountMin') }}</label>
            <InputNumber v-model="form.match_amount_min" mode="decimal" :minFractionDigits="2" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('rules.amountMax') }}</label>
            <InputNumber v-model="form.match_amount_max" mode="decimal" :minFractionDigits="2" class="w-full" />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">{{ t('rules.priority') }}</label>
          <InputNumber v-model="form.priority" class="w-full" />
        </div>

        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="form.is_active" />
          <label class="text-sm">{{ t('rules.active') }}</label>
        </div>
      </div>

      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" text @click="dialogVisible = false" />
        <Button :label="t('common.save')" @click="saveRule" />
      </template>
    </Dialog>
  </div>
</template>
