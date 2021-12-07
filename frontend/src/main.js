import Vue from 'vue'
import App from './App.vue'
import './assets/style.scss';

import { make_i18n_jsons } from './utils/export_i18n_csv';
make_i18n_jsons("./locales/translations.csv", "./locales/json")

import i18n from './i18n';


import moment from 'moment';
moment.locale(window.navigator.userLanguage || window.navigator.language || 'en');
moment.tz.setDefault(moment.tz.guess());
Vue.use(require('vue-moment'), {moment});

import VueRouter from 'vue-router';
import router from './router';
Vue.use(VueRouter);

import store from './store';

import Buefy from 'buefy';
Vue.use(Buefy, {defaultIconPack: 'fas'});

import axios from 'axios';
axios.defaults.baseURL = process.env.VUE_APP_API;

Vue.config.productionTip = false;

new Vue({
  render: h => h(App),
  i18n,
  router,
  store
}).$mount('#app');
