<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

import { ref } from 'vue';
const username = ref('');
const password = ref('');

const login = () => {
  console.log('Login', username.value, password.value);
};
</script>

<template>
  <main class="flex items-center justify-center min-h-screen">
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
          <Button class="w-full" @click="login">{{ t('login.title')}}</Button>
        </div>
      </form>
    </div>
  </main>
</template>

