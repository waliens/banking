import Vue from 'vue'
import App from './App.vue'
import './assets/style.scss';

import i18n from './i18n';

import moment from 'moment';
moment.locale(window.navigator.userLanguage || window.navigator.language || 'en');
Vue.use(require('vue-moment'), {moment});

import VueRouter from 'vue-router';
import router from './router';
Vue.use(VueRouter);

import store from './store';

import Buefy from 'buefy';
Vue.use(Buefy, {defaultIconPack: 'fas'});

import VueGoogleCharts from 'vue-google-charts' 
Vue.use(VueGoogleCharts)

Vue.config.productionTip = false;

new Vue({
  render: h => h(App),
  i18n,
  router,
  store
}).$mount('#app');
