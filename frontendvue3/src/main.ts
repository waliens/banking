import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'

import en from './i18n/json/en.json'
import fr from './i18n/json/fr.json'
const i18n = createI18n({
  fallbackLocale: 'en',
  locale: 'en',
  messages: { en, fr }
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
