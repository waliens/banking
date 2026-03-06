<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCategoryStore } from '../../stores/categories'
import { contrastText } from '../../utils/color'
import InputText from 'primevue/inputtext'

const props = defineProps({
  modelValue: { type: [Number, Array], default: null },
  placeholder: { type: String, default: 'Select category' },
  showClear: { type: Boolean, default: false },
  multiple: { type: Boolean, default: false },
  categories: { type: Array, default: null },
})

const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()
const categoryStore = useCategoryStore()
const isOpen = ref(false)
const searchQuery = ref('')
const rootRef = ref(null)
const triggerRef = ref(null)
const dropdownRef = ref(null)
const dropdownStyle = ref({})

// Single-select: selected category object
const selectedCategory = computed(() => {
  if (props.multiple || props.modelValue == null) return null
  return categoryStore.categoryMap.get(props.modelValue)
})

// Multi-select: set for fast lookup
const selectedSet = computed(() => {
  if (!props.multiple || !Array.isArray(props.modelValue)) return new Set()
  return new Set(props.modelValue)
})

// Source tree: use custom categories prop or store tree
const sourceTree = computed(() => {
  if (props.categories) return props.categories
  return categoryStore.categoryTree
})

// Filtered tree: top-level groups with no matching children are hidden entirely
const filteredTree = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return sourceTree.value
  return sourceTree.value
    .map((parent) => ({
      ...parent,
      children: (parent.children || []).filter((child) =>
        child.name.toLowerCase().includes(q),
      ),
    }))
    .filter((parent) => parent.children.length > 0)
})

// All selectable child ids from the current tree
const allChildIds = computed(() => {
  const ids = []
  for (const parent of sourceTree.value) {
    for (const child of parent.children || []) {
      ids.push(child.id)
    }
  }
  return ids
})

// Trigger display text for multi-select
const triggerDisplay = computed(() => {
  if (!props.multiple) return null
  const selected = props.modelValue || []
  if (selected.length === 0) return props.placeholder
  if (selected.length <= 2) {
    return selected
      .map((id) => categoryStore.categoryMap.get(id)?.name || id)
      .join(', ')
  }
  return t('wallet.categoriesSelected', { n: selected.length })
})

function select(category) {
  if (props.multiple) {
    toggleMulti(category.id)
  } else {
    emit('update:modelValue', category.id)
    isOpen.value = false
  }
}

function toggleMulti(id) {
  const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  const idx = current.indexOf(id)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(id)
  }
  emit('update:modelValue', current)
}

function selectAllCategories() {
  emit('update:modelValue', [...allChildIds.value])
}

function deselectAllCategories() {
  emit('update:modelValue', [])
}

function clear() {
  if (props.multiple) {
    emit('update:modelValue', [])
  } else {
    emit('update:modelValue', null)
  }
}

async function open() {
  isOpen.value = true
  searchQuery.value = ''
  await nextTick()
  if (triggerRef.value) {
    const rect = triggerRef.value.getBoundingClientRect()
    dropdownStyle.value = {
      top: `${rect.bottom + 4}px`,
      left: `${rect.left}px`,
      width: `${Math.max(rect.width, 220)}px`,
    }
  }
}

function handleClickOutside(event) {
  if (
    rootRef.value && !rootRef.value.contains(event.target) &&
    (!dropdownRef.value || !dropdownRef.value.contains(event.target))
  ) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div ref="rootRef" class="relative">
    <!-- Trigger -->
    <button
      ref="triggerRef"
      type="button"
      @click="isOpen ? (isOpen = false) : open()"
      class="w-full flex items-center justify-between gap-2 px-3 py-2
             border border-surface-200 rounded-lg bg-surface-0
             hover:border-surface-300 transition-colors cursor-pointer text-left text-sm"
    >
      <div class="flex items-center gap-2 min-w-0 flex-1 truncate">
        <!-- Single-select display -->
        <template v-if="!multiple">
          <i
            v-if="selectedCategory?.icon"
            :class="selectedCategory.icon"
            class="text-sm shrink-0"
            :style="selectedCategory.color ? { color: contrastText(selectedCategory.color) } : {}"
          />
          <span :class="selectedCategory ? 'text-surface-900' : 'text-surface-400'">
            {{ selectedCategory?.name || placeholder }}
          </span>
        </template>
        <!-- Multi-select display -->
        <template v-else>
          <span :class="(modelValue && modelValue.length) ? 'text-surface-900' : 'text-surface-400'">
            {{ triggerDisplay }}
          </span>
        </template>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <button
          v-if="showClear && (multiple ? modelValue?.length : modelValue != null)"
          @click.stop="clear"
          type="button"
          class="text-surface-400 hover:text-surface-600 transition-colors"
        >
          <i class="pi pi-times text-xs"></i>
        </button>
        <i class="pi pi-chevron-down text-xs text-surface-400"></i>
      </div>
    </button>

    <!-- Dropdown — teleported to body to escape any overflow/z-index clipping -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="dropdownRef"
        :style="dropdownStyle"
        class="fixed z-[9999] min-w-[220px] bg-surface-0 border border-surface-200 rounded-lg shadow-xl overflow-hidden"
      >
        <!-- Search -->
        <div class="p-2 border-b border-surface-100">
          <InputText
            v-model="searchQuery"
            placeholder="Search categories…"
            class="w-full text-sm"
            autofocus
          />
        </div>

        <!-- Select all / Deselect all (multi-select only) -->
        <div v-if="multiple" class="flex gap-2 px-3 py-1.5 border-b border-surface-100">
          <button
            @click="selectAllCategories"
            type="button"
            class="text-xs text-primary-600 hover:text-primary-800 transition-colors"
          >
            {{ t('wallet.selectAll') }}
          </button>
          <span class="text-surface-300">|</span>
          <button
            @click="deselectAllCategories"
            type="button"
            class="text-xs text-primary-600 hover:text-primary-800 transition-colors"
          >
            {{ t('wallet.deselectAll') }}
          </button>
        </div>

        <!-- Hierarchical list -->
        <div class="overflow-y-auto max-h-72">
          <template v-for="parent in filteredTree" :key="parent.id">
            <!-- Group header — non-selectable separator -->
            <div class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-surface-400 bg-surface-50 uppercase tracking-wide select-none">
              <i
                v-if="parent.icon"
                :class="parent.icon"
                class="text-sm"
                :style="parent.color ? { color: contrastText(parent.color) } : {}"
              />
              {{ parent.name }}
            </div>
            <!-- Leaf children — selectable -->
            <div
              v-for="child in parent.children"
              :key="child.id"
              @click="select(child)"
              class="flex items-center gap-2 pl-5 pr-3 py-2 hover:bg-surface-100 cursor-pointer text-sm transition-colors"
              :class="(!multiple && modelValue === child.id) ? 'bg-primary-50 text-primary-700' : (multiple && selectedSet.has(child.id)) ? 'bg-primary-50 text-primary-700' : 'text-surface-900'"
            >
              <!-- Multi-select checkbox -->
              <i
                v-if="multiple"
                :class="selectedSet.has(child.id) ? 'pi pi-check-square text-primary-500' : 'pi pi-stop text-surface-300'"
                class="text-sm shrink-0"
              />
              <i
                v-if="child.icon"
                :class="child.icon"
                class="text-sm shrink-0"
                :style="child.color ? { color: contrastText(child.color) } : {}"
              />
              <span class="flex-1">{{ child.name }}</span>
              <i v-if="!multiple && modelValue === child.id" class="pi pi-check text-primary-500 text-xs shrink-0" />
            </div>
          </template>

          <div v-if="filteredTree.length === 0" class="px-3 py-3 text-xs text-surface-400 text-center">
            No categories found
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
