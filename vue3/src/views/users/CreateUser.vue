<script setup>
import { ref } from 'vue';
import CreateEditUser from '@/components/user/CreateEditUser.vue';
import { useI18n } from 'vue-i18n';
import User from '@/data/models/user';

const { t } = useI18n();
const user = ref(new User());  
</script>

<template>
  <create-edit-user :user="user" />
</template>