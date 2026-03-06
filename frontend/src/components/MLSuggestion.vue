<script setup>
import { computed } from 'vue'
import { contrastText } from '../utils/color'

const props = defineProps({
  categoryName: { type: String, default: null },
  categoryColor: { type: String, default: null },
  probability: { type: Number, default: 0 },
})

const emit = defineEmits(['accept'])

const textColor = computed(() => contrastText(props.categoryColor))
</script>

<template>
  <button
    v-if="categoryName"
    class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium cursor-pointer hover:opacity-80 transition-opacity"
    :style="{ backgroundColor: categoryColor + '20', color: textColor, border: `1px solid ${categoryColor}40` }"
    :title="`Accept suggestion: ${categoryName}`"
    @click="emit('accept')"
  >
    <i class="pi pi-sparkles text-[10px]" />
    <span>{{ categoryName }}</span>
    <span class="opacity-60">{{ Math.round(probability * 100) }}%</span>
  </button>
</template>
