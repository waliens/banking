<script setup>
defineProps({
  account: { type: Object, default: null }
})
</script>

<template>
  <div>
    <div class="font-medium">{{ account?.name || '—' }}</div>
    <div class="text-xs text-surface-400">{{ account?.number || '—' }}</div>
  </div>
</template>
