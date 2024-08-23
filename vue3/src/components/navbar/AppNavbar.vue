<script setup lang="ts">
import { ref } from 'vue';
import Menubar from 'primevue/menubar';

import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const items = ref([
  {
    label: t('dashboard'),
    icon: 'fa fa-chart-pie',
    // routerLink: { name: 'dashboard' }
  },
  {
    label: t('account_group.groups'),
    icon: 'fa fa-user',
    // routerLink: { name: 'select-account-group' }
  },
  {
    label: t('tagging.title'),
    icon: 'fa fa-tag',
    // routerLink: { name: 'transactions-tagging' }
  },
  {
    label: t('transaction.title'),
    icon: 'fa-solid fa-plus',
    items: [
      {
        label: t('data_upload.title'),
        icon: 'fa fa-upload',
        // routerLink: { name: 'upload-data' }
      },
      {
        label: t('data_upload.manual'),
        icon: 'fa fa-hand',
        // routerLink: { name: 'create-transaction' }
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
        // routerLink: { name: 'edit-tag-tree' }
      },
      {
        label: t('account.merge'),
        icon: 'fa fa-tags',
        // routerLink: { name: 'merge-accounts' }
      },
      {
        label: t('ml_model.title'),
        icon: 'fa fa-hat-wizard',
        // routerLink: { name: 'models' }
      },
      {
        label: t('navbar.manage_duplicate'),
        icon: 'fa fa-copy',
        // routerLink: { name: 'manage-duplicate-transactions' }
      },
      {
        label: t('users.manage'),
        icon: 'fa fa-users',
        // routerLink: { name: 'manage-users' }
      }
    ]
  },
  {
    label: t('help'),
    icon: 'fa fa-question-circle',
    // routerLink: { name: 'help' }
  }
]);

const username = ref("test");
</script>

<template>
  
  <Menubar :model="items" class="m-4">
    <template #start>
      <RouterLink to="/" class="p-mr-2">
        {{t('app-name')}}
      </RouterLink>
    </template>
    <template #end>
      <div class="flex items-center gap-2">
        <Avatar v-tooltip.left="username" :label="username[0].toUpperCase()" class="mr-2" shape="circle" />
        <Button v-tooltip.left="t('logout.title')" icon="fa fa-right-from-bracket" class="p-button-rounded p-button-text" severity="danger" />
      </div>
    </template>
  </Menubar>

</template>