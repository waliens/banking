import { createApp } from 'vue'
import router from './router'
import PrimeVue from 'primevue/config';
import Aura from '@primevue/themes/aura';

import { createI18n } from 'vue-i18n'
import en from '@/i18n/json/en.json'
import fr from '@/i18n/json/fr.json'

import '@/assets/style.css'
import App from '@/App.vue'

const i18n = createI18n({
  legacy: false,
  fallbackLocale: 'en',
  locale: 'en',
  messages: { en, fr }
})

const app = createApp(App)

app.use(router)
app.use(i18n)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: 'system',
      cssLayer: false
    }
  }
})

app.mount('#app')
