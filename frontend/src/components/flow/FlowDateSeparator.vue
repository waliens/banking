<script setup>
defineProps({
  label: { type: String, required: true },
})
</script>

<template>
  <div class="col-span-full flex items-center gap-3 py-4">
    <div class="flex-1 border-t border-surface-200"></div>
    <span class="text-sm font-semibold text-surface-500 whitespace-nowrap">{{ label }}</span>
    <div class="flex-1 border-t border-surface-200"></div>
  </div>
</template>
