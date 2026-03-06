<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch {
    error.value = t('auth.loginError')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-100">
    <div class="w-full max-w-sm bg-surface-0 rounded-xl shadow-lg p-8">
      <h1 class="text-2xl font-bold text-center mb-6">Banking</h1>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label for="username" class="text-sm font-medium">{{ t('auth.username') }}</label>
          <InputText id="username" v-model="username" autocomplete="username" class="w-full" />
        </div>

        <div class="flex flex-col gap-1">
          <label for="password" class="text-sm font-medium">{{ t('auth.password') }}</label>
          <Password id="password" v-model="password" :feedback="false" toggleMask autocomplete="current-password" input-class="w-full" class="w-full" />
        </div>

        <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>

        <Button type="submit" :label="t('auth.login')" :loading="loading" class="w-full" />
      </form>
    </div>
  </div>
</template>
