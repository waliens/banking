<script setup>
import { useRoute } from 'vue-router';
import CreateEditUser from '@/components/user/CreateEditUser.vue';
import { computed, onMounted } from 'vue';
import { useUsersStore } from '@/stores/users';

const route = useRoute();
const users_store = useUsersStore();

const route_user = computed(() => {
  return users_store.get_user_by_id(route.params.id);
});

</script>

<template>
  <create-edit-user :user="route_user" />
</template>