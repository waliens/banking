<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCategoryStore } from '../../stores/categories'
import { useToast } from 'primevue/usetoast'
import Tree from 'primevue/tree'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import ColorPicker from 'primevue/colorpicker'
import Select from 'primevue/select'
import IconPicker from '../common/IconPicker.vue'

const { t } = useI18n()
const toast = useToast()
const categoryStore = useCategoryStore()

const showDialog = ref(false)
const editingCategory = ref(null)
const form = ref({ name: '', color: '#3B82F6', id_parent: null, icon: null })

function buildTreeNodes(nodes) {
  return nodes.map((node) => ({
    key: node.id,
    label: node.name,
    data: node,
    children: node.children?.length ? buildTreeNodes(node.children) : undefined,
    style: `border-left: 4px solid ${node.color || '#ccc'}`,
  }))
}

function openCreate(parentId = null) {
  editingCategory.value = null
  form.value = { name: '', color: '#3B82F6', id_parent: parentId, icon: null }
  showDialog.value = true
}

function openEdit(category) {
  editingCategory.value = category
  form.value = {
    name: category.name,
    color: category.color?.replace('#', '') || '3B82F6',
    id_parent: category.id_parent,
    icon: category.icon,
  }
  showDialog.value = true
}

async function save() {
  const payload = {
    ...form.value,
    color: form.value.color.startsWith('#') ? form.value.color : `#${form.value.color}`,
  }

  try {
    if (editingCategory.value) {
      await categoryStore.updateCategory(editingCategory.value.id, payload)
    } else {
      await categoryStore.createCategory(payload)
    }
    showDialog.value = false
    await categoryStore.fetchCategories()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Failed', life: 3000 })
  }
}

async function handleDelete(category) {
  if (!confirm(`Delete category "${category.name}"?`)) return
  await categoryStore.deleteCategory(category.id)
  await categoryStore.fetchCategories()
}

onMounted(() => categoryStore.fetchCategories())
</script>

<template>
  <div>
    <div class="flex justify-end mb-4">
      <Button :label="t('common.create')" icon="pi pi-plus" @click="openCreate()" size="small" />
    </div>

    <div class="bg-surface-0 rounded-xl shadow p-4">
      <Tree :value="buildTreeNodes(categoryStore.categoryTree)" class="w-full">
        <template #default="{ node }">
          <div class="flex items-center justify-between w-full gap-2">
            <div class="flex items-center gap-2">
              <i v-if="node.data.icon" :class="node.data.icon" />
              <span>{{ node.label }}</span>
            </div>
            <div class="flex gap-1">
              <Button icon="pi pi-plus" text rounded size="small" @click.stop="openCreate(node.data.id)" />
              <Button icon="pi pi-pencil" text rounded size="small" @click.stop="openEdit(node.data)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click.stop="handleDelete(node.data)" />
            </div>
          </div>
        </template>
      </Tree>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingCategory ? t('common.edit') : t('common.create')" modal class="w-full max-w-md">
      <div class="flex flex-col gap-4 pt-2">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('categories.name') }}</label>
          <InputText v-model="form.name" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('categories.color') }}</label>
          <ColorPicker v-model="form.color" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('categories.parent') }}</label>
          <Select
            v-model="form.id_parent"
            :options="categoryStore.categories"
            optionLabel="name"
            optionValue="id"
            :showClear="true"
            placeholder="None (root)"
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('categories.icon') }}</label>
          <IconPicker v-model="form.icon" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDialog = false" />
        <Button :label="t('common.save')" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
