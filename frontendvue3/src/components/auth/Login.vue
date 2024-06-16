<!-- src/components/Login.vue -->
<template>
  <form @submit.prevent="submit">
    <input v-model="credentials.username" type="text" placeholder="Username" />
    <input v-model="credentials.password" type="password" placeholder="Password" />
    <button type="submit">Login</button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const credentials = ref({ username: '', password: '' });

const submit = () => {
  auth.login(credentials.value);
};
</script>