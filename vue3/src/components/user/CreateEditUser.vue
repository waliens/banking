
<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import User from '@/data/models/user';

const { t } = useI18n()

defineProps({
  user: {
    type: User
  }, 
})
</script>

<template>
  <form>
    <section class="w-full">
      <div class="grid grid-cols-6 gap-2">
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.username')}}</label></div>
        <div class="col-span-5"><InputText v-model="user.username" class="w-full"></InputText></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.password')}}</label></div>
        <div class="col-span-5"><Password v-model="user.password" toggleMask class="w-full" inputClass="w-full"></Password></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.repeat_password')}}</label></div>
        <div class="col-span-5"><Password v-model="user.password2" toggleMask class="w-full" inputClass="w-full"></Password></div>
        <div class="col-span-6 flex flex-row-reverse">
          <Button  icon-right="save">{{t('save')}}</Button>
        </div>
      </div>
    </section>
  </form>
</template>

