<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import router from '@/router';
import { RouterView } from 'vue-router';
import { useUsersStore } from '@/stores/users';

const usersStore = useUsersStore();
const { t } = useI18n();

const menuItems = computed(() => {
  return [
    {
      label: t('user.create'),
      icon: 'fa fa-plus',
      command: () => router.push({ name: 'create-user' })
    },
    { 
      label: t('users.title'),
      icon: 'fa fa-users',
      items: usersStore.users.map(u => {
        return {
          label: u.username,
          icon: 'fa fa-user',
          command: () => router.push({ name: 'edit-user', params: { id: u.id } })
        };
      })
    }
  ];
});

</script>

<template>
  <div class="flex flex-rows flex-auto">
    <section>
      <Menu class="scrollable p-2" :model="menuItems" >
        <template #start>
          <div class="container flex flew-row justify-center">
            <h1 class="font-bold"><i class="fa fa-users mr-3"></i> {{ t('users.manage') }}</h1>
          </div>
        </template>
      </Menu>
    </section>
    <section class="ml-4 w-full">
      <RouterView />
    </section>
  </div>
</template>