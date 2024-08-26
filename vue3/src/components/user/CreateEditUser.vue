
<script setup>
import { defineProps, ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

import { useUsersStore } from '@/stores/users';
import User from '@/data/models/user';
import UserService from '@/data/services/user_service';

const { t } = useI18n()
const router = useRouter();
const usersStore = useUsersStore();
const toast = useToast();

const props = defineProps({
  user: {
    type: User
  }, 
});

// let's not mutate the props.user here and use a mutable copy
const mutable_user = ref({ ...props.user });
watch(
  () => props.user,
  (newUser) => {
    mutable_user.value = new User({ ...newUser });
  },
  { immediate: true }
);

const save = async () => {
  const user_service = new UserService();
  if (mutable_user.value.id) {
    console.log(mutable_user.value.username)
    let updated_user = await user_service.update(mutable_user.value.id, mutable_user.value);
    usersStore.update_user(updated_user);
    router.push({ name: 'edit-user', params: { id: updated_user.id } });
    toast.add({ severity: 'success', summary: t('success'), detail: t('user.updated') });
  } else {
    let new_user = await user_service.create(mutable_user.value);
    usersStore.add_user(new_user);
    router.push({ name: 'edit-user', params: { id: new_user.id } });
    toast.add({ severity: 'success', summary: t('success'), detail: t('user.created') });
  }
}

const valid_password = computed(() => {
  return (!mutable_user.value.password && !mutable_user.value.password2) 
    || (mutable_user.value.password === mutable_user.value.password2 && mutable_user.value.password.length > 0);
});

const valid_username = computed(() => {
  return mutable_user.value.username && mutable_user.value.username.length > 0;
});

</script>

<template>
  <Form>
    <Toast />
    <section class="w-full">
      <div class="grid grid-cols-6 gap-2">
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.username')}}</label></div>
        <div class="col-span-5"><InputText v-model="mutable_user.username" fluid :invalid="!valid_username"></InputText></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.password')}}</label></div>
        <div class="col-span-5"><Password v-model="mutable_user.password" toggleMask fluid :invalid="!valid_password"></Password></div>
        <div class="col-span-1 content-evenly flex flex-row-reverse"><label class="self-center">{{t('user.repeat_password')}}</label></div>
        <div class="col-span-5"><Password v-model="mutable_user.password2" toggleMask fluid :invalid="!valid_password"></Password></div>
        <div class="col-span-6 flex flex-row-reverse">
          <Button :disabled="!valid_password || !valid_username" @click="save" icon-right="save">{{mutable_user.id ? t('save') : t('create')}}</Button>
        </div>
      </div>
    </section>
  </Form>
</template>

