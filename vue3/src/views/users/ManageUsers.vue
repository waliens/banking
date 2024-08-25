<script setup>
import { onMounted, ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import router from '@/router';
import { RouterView } from 'vue-router';
import { useUsersStore } from '@/stores/users';

onMounted(async () => {
  await usersStore.update_users();
});

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
  <div class="grid grid-cols-4 gap-x-4">
    <section class="col-span-1">
      <Menu class="scrollable p-2" :model="menuItems" >
        <template #start>
          <div class="container flex flew-row justify-center">
            <h1 class="font-bold"><i class="fa fa-users mr-3"></i> {{ t('users.manage') }}</h1>
          </div>
        </template>
      </Menu>
    </section>
    <section class="w-full col-span-3">
      <RouterView />
    </section>
    <!-- <section class="col-span-3">
      <section class="flex items-center justify-between">
        <h3 class="text-xl">
          <span v-if="activeUser && activeUser.id">{{ t('user.edit') }}</span>
          <span v-else>{{ t('user.create') }}</span>
        </h3>
        <Button :disabled="!isFormValid()" class="is-small is-primary" @click="saveUser" icon="pi pi-save">{{t('save')}}</Button>
      </section>
      <section v-if="isAnyUserMenuActive">
        <Field :label="t('user.username')" label-position="on-border" :class="{ 'is-danger': activeUser.username.length === 0 }">
          <Input v-model="activeUser.username"></Input>
        </Field>
        <Field :label="t('user.password')" label-position="on-border" :class="{ 'is-danger': !passwordDoMatch }">
          <Input type="password" v-model="activeUser.password"></Input>
        </Field>
        <Field :label="t('user.repeat_password')" label-position="on-border" :class="{ 'is-danger': !passwordDoMatch }">
          <Input type="password" v-model="activeUser.password2"></Input>
        </Field>
      </section>
    </section> -->
  </div>
</template>