<script setup>
import { ref } from 'vue';
import Menubar from 'primevue/menubar';
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router'

const { t, locale, availableLocales } = useI18n()
const auth_store = useAuthStore();
const router = useRouter();

const items = ref([
  {
    label: t('dashboard'),
    icon: 'fa fa-chart-pie',
    command: () => router.push({ 'name': 'dashboard' })
  },
  {
    label: t('account_group.groups'),
    icon: 'fa fa-user',
    command: () => router.push({ 'name': 'select-account-group' })
  },
  {
    label: t('tagging.title'),
    icon: 'fa fa-tag',
    command: () => router.push({ 'name': 'transactions-tagging' })
  },
  {
    label: t('transaction.title'),
    icon: 'fa-solid fa-plus',
    items: [
      {
        label: t('data_upload.title'),
        icon: 'fa fa-upload',
        command: () => router.push({ 'name': 'upload-data' })
      },
      {
        label: t('data_upload.manual'),
        icon: 'fa fa-hand',
        command: () => router.push({ 'name': 'create-transaction' })
      }
    ]
  },
  {
    label: t('navbar.data'),
    icon: 'fa fa-pen',
    items: [
      {
        label: t('tagging.tree'),
        icon: 'fa fa-sitemap',
        command: () => router.push({ 'name': 'edit-tag-tree' })
      },
      {
        label: t('account.merge'),
        icon: 'fa fa-tags',
        command: () => router.push({ 'name': 'merge-accounts' })
      },
      {
        label: t('ml_model.title'),
        icon: 'fa fa-hat-wizard',
        command: () => router.push({ 'name': 'models' })
      },
      {
        label: t('navbar.manage_duplicate'),
        icon: 'fa fa-copy',
        command: () => router.push({ 'name': 'manage-duplicate-transactions' })
      },
      {
        label: t('users.manage'),
        icon: 'fa fa-users',
        command: () => router.push({ 'name': 'manage-users' })
      }
    ]
  },
  {
    label: t('help'),
    icon: 'fa fa-question-circle',
    command: () => router.push({ 'name': 'help' })
  }
]);

function get_username() {
  return auth_store.user?.username;
}

function get_username_first_letter() {
  return get_username()?.charAt(0).toUpperCase();
}

function logout() {
  auth_store.logout();
  router.push({ 'name': 'login' });
}
</script>

<template>
  <Menubar :model="items" class="mb-4">
    <template #start>
      <RouterLink to="/" class="p-mr-2">
        <span class="px-4 font-bold">{{t('app-name')}}</span>
      </RouterLink>
    </template>
    <template #end>
      <div class="flex items-center gap-2">
        <!-- Because t() is not reactive, this does not trigger a direct change of names 
        <Select v-model="locale" :options="availableLocales" disabled >
          <template #value="props">
            {{ !!props.value ? props.value.toUpperCase() : '' }}
          </template>
          <template #option="props">
            {{ !!props.option ? props.option.toUpperCase() : '' }}
          </template>
        </Select>
        -->
        <Avatar class="mr-2" shape="circle" v-tooltip.left="get_username()" :label="get_username_first_letter()" />
        <Button
          v-tooltip.left="t('logout.title')"
          icon="fa fa-right-from-bracket"
          class="p-button-rounded p-button-text"
          severity="danger"
          @click="logout" />
      </div>
    </template>
  </Menubar>

</template>