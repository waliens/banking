<script setup>
import { defineProps } from 'vue';
const props = defineProps({
  items: { type: Array },
  title: { type: String },
  titleIcon: { type: String, default: '' }
})
</script>

<template>
  <Menu :items="items">
    <template #start>
      <div class="p-d-flex p-ai-center">
        <i :class="titleIcon" class="p-mr-2"></i>
        <h1 class="font-bold">{{ title }}</h1>
      </div>
    </template>
  </Menu>
</template>