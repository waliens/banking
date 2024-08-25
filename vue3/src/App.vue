<script setup>
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUsersStore } from '@/stores/users';

// Move the await statement inside a lifecycle hook or a separate function
onMounted(async () => {
  const stores = [
    useAuthStore(),
    useUsersStore()
  ];
  await Promise.all(stores.map(store => store.init()));
});
</script>

<template>
  <RouterView/>
</template>

