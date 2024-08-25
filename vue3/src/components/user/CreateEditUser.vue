
<script setup>
import { useI18n } from 'vue-i18n';
import User from '@/data/models/user';
import UserService from '@/data/services/user_service';
import { useUsersStore } from '@/stores/users';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

const { t } = useI18n()
const router = useRouter();
const usersStore = useUsersStore();
const toast = useToast();

const props = defineProps({
  user: {
    type: User
  }, 
})

const save = async () => {
  const user_service = new UserService();
  const user = props.user;
  let id = user.id;
  if (user.id) {
    await user_service.update(user.id, user);
    usersStore.update_user(user);
    router.push({ name: 'edit-user', params: { id: user.id } });
    toast.add({ severity: 'success', summary: t('success'), detail: t('user.updated') });
  } else {
    let new_user = await user_service.create(user);
    usersStore.add_user(new_user);
    router.push({ name: 'edit-user', params: { id: new_user.id } });
    toast.add({ severity: 'success', summary: t('success'), detail: t('user.created') });
  }
} 
</script>

<template>
  <form>
    <Toast />
    <section class="w-full">
      <div class="grid grid-cols-6 gap-2">
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.username')}}</label></div>
        <div class="col-span-5"><InputText v-model="user.username" class="w-full"></InputText></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.password')}}</label></div>
        <div class="col-span-5"><Password v-model="user.password" toggleMask class="w-full" inputClass="w-full"></Password></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.repeat_password')}}</label></div>
        <div class="col-span-5"><Password v-model="user.password2" toggleMask class="w-full" inputClass="w-full"></Password></div>
        <div class="col-span-6 flex flex-row-reverse">
          <Button @click="save" icon-right="save">{{user.id ? t('save') : t('create')}}</Button>
        </div>
      </div>
    </section>
  </form>
</template>

