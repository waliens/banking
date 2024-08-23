import { createApp } from 'vue'
import '@/assets/style.css'
import App from '@/App.vue'

const app = createApp(App)

// router
import router from './router'
app.use(router)

// i18n
import { createI18n } from 'vue-i18n'
import en from '@/i18n/json/en.json'
import fr from '@/i18n/json/fr.json'
const i18n = createI18n({
  legacy: false,
  fallbackLocale: 'en',
  locale: 'en',
  messages: { en, fr }
})
app.use(i18n)

// fontawesome
// https://stackoverflow.com/a/71672141
import { library, dom } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { fas } from '@fortawesome/free-solid-svg-icons'
import { fab } from '@fortawesome/free-brands-svg-icons';
import { far } from '@fortawesome/free-regular-svg-icons';

library.add(fas, fab, far);
dom.watch()
app.component("font-awesome-icon", FontAwesomeIcon)

// primevue
import PrimeVue from 'primevue/config';
import 'primeicons/primeicons.css'
import Aura from '@primevue/themes/aura';
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

/* ***** */
app.mount('#app')
