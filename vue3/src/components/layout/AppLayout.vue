<script setup>
import { RouterView } from 'vue-router';
import AppNavbar from '@/components/navbar/AppNavbar.vue';
</script>

<template>
  <div class="m-4">
    <AppNavbar />
    <main>
      <RouterView />
    </main>
  </div>
</template>
