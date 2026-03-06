<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Chart from 'primevue/chart'
import SelectButton from 'primevue/selectbutton'
import Button from 'primevue/button'
import CategorySelect from '../common/CategorySelect.vue'

const props = defineProps({
  data: { type: Object, default: null },
  title: { type: String, default: '' },
  categoryTree: { type: Array, default: () => [] },
  categoryMap: { type: Map, default: () => new Map() },
})

const { t } = useI18n()

const defaultColors = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16', '#a855f7', '#f43f5e']

const levelMode = ref('coarse')
const drillParentId = ref(null)
const selectedCategoryIds = ref([])

const levelOptions = [
  { label: t('wallet.levelCoarse'), value: 'coarse' },
  { label: t('wallet.levelFine'), value: 'fine' },
]

// Get parent category info for drilled view
const drilledParent = computed(() => {
  if (drillParentId.value == null) return null
  return props.categoryMap.get(drillParentId.value)
})

// Aggregate items into coarse (parent-level) buckets
function aggregateToParents(items) {
  const buckets = new Map()
  for (const item of items) {
    let parentId = item.id_parent || item.id_category
    // If this category IS a parent (no id_parent), use itself
    if (item.id_parent == null) {
      parentId = item.id_category
    }
    const key = parentId || '__uncategorized__'
    if (!buckets.has(key)) {
      const parentCat = parentId != null ? props.categoryMap.get(parentId) : null
      buckets.set(key, {
        id_category: parentId,
        category_name: parentCat?.name || t('wallet.uncategorized'),
        category_color: parentCat?.color || null,
        amount: 0,
      })
    }
    buckets.get(key).amount += Number(item.amount)
  }
  return [...buckets.values()].sort((a, b) => b.amount - a.amount)
}

// Get children of a specific parent from the raw data
function getChildrenOf(parentId, items) {
  return items.filter((item) => {
    if (item.id_parent === parentId) return true
    if (item.id_category === parentId && item.id_parent == null) return true
    return false
  })
}

// Visible items based on level mode and drill state
const visibleItems = computed(() => {
  if (!props.data?.items?.length) return []
  const items = props.data.items

  if (drillParentId.value != null) {
    // Show children of drilled parent
    return getChildrenOf(drillParentId.value, items)
  }

  if (levelMode.value === 'coarse') {
    return aggregateToParents(items)
  }

  // Fine mode: show raw items
  return items
})

// Categories available for the filter based on current view
const filterCategories = computed(() => {
  if (drillParentId.value != null) {
    // When drilled: show only the drilled parent's children from tree
    const parent = props.categoryTree.find((p) => p.id === drillParentId.value)
    return parent ? [parent] : []
  }
  if (levelMode.value === 'coarse') {
    // In coarse mode: show parent categories as "children" of a virtual root
    const parentIds = new Set(visibleItems.value.map((i) => i.id_category).filter((id) => id != null))
    const fakeTree = [{
      id: '__all__',
      name: t('wallet.level'),
      children: [...parentIds].map((id) => {
        const cat = props.categoryMap.get(id)
        return cat ? { ...cat } : { id, name: String(id) }
      }),
    }]
    return fakeTree
  }
  // Fine mode: use the full tree
  return props.categoryTree
})

// Reset selected categories when view changes
watch([levelMode, drillParentId, () => props.data], () => {
  const ids = visibleItems.value
    .map((i) => i.id_category)
    .filter((id) => id != null)
  selectedCategoryIds.value = ids
}, { immediate: true })

// Filtered visible items by selected categories
const filteredItems = computed(() => {
  const selected = new Set(selectedCategoryIds.value)
  return visibleItems.value.filter((item) => {
    if (item.id_category == null) return true // always show uncategorized
    return selected.has(item.id_category)
  })
})

const chartData = computed(() => {
  if (!filteredItems.value.length) return null
  const items = filteredItems.value
  return {
    labels: items.map((i) => i.category_name || t('wallet.uncategorized')),
    datasets: [
      {
        data: items.map((i) => Number(i.amount)),
        backgroundColor: items.map((i, idx) => i.category_color || defaultColors[idx % defaultColors.length]),
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'right',
      labels: { padding: 16 },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const item = filteredItems.value[ctx.dataIndex]
          const parentName = item.id_parent != null ? props.categoryMap.get(item.id_parent)?.name : null
          const prefix = parentName ? `${parentName} > ` : ''
          return `${prefix}${item.category_name || t('wallet.uncategorized')}: ${Number(item.amount).toFixed(2)}`
        },
      },
    },
  },
  onClick: (_event, elements) => {
    if (elements.length === 0 || levelMode.value === 'fine') return
    const idx = elements[0].index
    const item = filteredItems.value[idx]
    if (item?.id_category != null && drillParentId.value == null) {
      drillParentId.value = item.id_category
    }
  },
}))

function goBack() {
  drillParentId.value = null
}
</script>

<template>
  <div>
    <!-- Title + controls -->
    <div class="flex flex-wrap items-center gap-3 mb-3">
      <h3 class="text-lg font-semibold">{{ title }}</h3>
      <SelectButton
        v-model="levelMode"
        :options="levelOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
        class="text-sm"
      />
      <Button
        v-if="drillParentId != null"
        :label="`${t('wallet.backToParent')}${drilledParent ? ': ' + drilledParent.name : ''}`"
        icon="pi pi-arrow-left"
        size="small"
        text
        @click="goBack"
      />
    </div>

    <!-- Category filter -->
    <div class="mb-3 max-w-xs">
      <CategorySelect
        v-model="selectedCategoryIds"
        :multiple="true"
        :categories="filterCategories"
        :placeholder="t('categories.selectCategory')"
        :showClear="true"
      />
    </div>

    <!-- Chart -->
    <div v-if="chartData" class="relative max-w-xl">
      <Chart type="doughnut" :data="chartData" :options="chartOptions" />
    </div>
    <p v-else class="text-surface-500 text-center py-8">{{ t('wallet.noData') }}</p>
  </div>
</template>
