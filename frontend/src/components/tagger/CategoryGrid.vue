<script setup>
import { contrastText } from '../../utils/color'

defineProps({
  categories: { type: Array, required: true },
  transaction: { type: Object, default: null },
})

const emit = defineEmits(['select'])

function categoryStyle(cat) {
  const color = cat.color || '#6366f1'
  return {
    borderLeftColor: color,
    backgroundColor: color + '10',
    color: contrastText(color),
  }
}
</script>

<template>
  <div>
    <!-- Transaction context card -->
    <div v-if="transaction" class="mb-4 p-3 bg-surface-100 rounded-lg text-sm">
      <div class="font-medium truncate">{{ transaction.description || '—' }}</div>
      <div class="flex justify-between mt-1 text-surface-500">
        <span>{{ transaction.date }}</span>
        <span :class="transaction.id_source ? 'text-red-500' : 'text-green-600'" class="font-medium">
          {{ transaction.id_source ? '-' : '+' }}{{ transaction.amount }}
        </span>
      </div>
    </div>

    <!-- Category grid -->
    <div class="grid grid-cols-3 sm:grid-cols-4 gap-2">
      <button
        v-for="cat in categories"
        :key="cat.id"
        class="flex items-center justify-center p-3 rounded-xl border-l-4 border border-surface-200 text-sm font-medium text-center min-h-[56px] hover:shadow-md active:scale-95 transition-all"
        :style="categoryStyle(cat)"
        @click="emit('select', cat.id)"
      >
        {{ cat.name }}
      </button>
    </div>
  </div>
</template>
