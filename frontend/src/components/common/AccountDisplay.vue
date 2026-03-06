<script setup>
defineProps({
  account: { type: Object, default: null },
  highlight: { type: Boolean, default: false },
})
</script>

<template>
  <div>
    <div class="font-medium" :class="highlight ? 'text-primary-600' : ''">{{ account?.name || '—' }}</div>
    <div class="text-xs text-surface-400">{{ account?.number || '—' }}</div>
  </div>
</template>
