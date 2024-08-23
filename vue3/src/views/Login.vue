<script setup>
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast';
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';

const { t } = useI18n()
const username = ref('');
const password = ref('');

const toast = useToast();


const login = async () => {
  const authStore = useAuthStore();
  await authStore.login(username, password).then(
    () => {
      this.$router.push('/');
    },
    () => {
      toast.add({
        severity: 'error',
        summary: t('error'),
        detail: t('login.invalid-username-or-password')
      });
    }
  );
};
</script>

<template>
  <main class="flex items-center justify-center min-h-screen">
    <Toast />
    <div class="w-5/12 p-5 ">
      <form class="container space-y-2">
        <div>
          <label for="username">{{ t('user.username') }}</label>
          <InputText id="username" v-model="username" class="w-full" />
        </div>
        <div>
          <label for="password">{{ t('user.password') }}</label>
          <Password id="password" v-model="password" inputClass="w-full" class="w-full" />
        </div>
        <div>
          <Button class="w-full" @click="login" :disabled="!username || !password">{{ t('login.title')}}</Button>
        </div>
      </form>
    </div>
  </main>
</template>

