import VueRouter from 'vue-router';
import store from './store';

const groupSelectedOnly = async (to, from, next) => {
  await store.dispatch('initializeStore');

  if (store.state.currentGroup) {
    next();
    return;
  }
  next({name: 'group_select'});
};

const routes = [
  {
    name: 'home',
    path: '/',
    component: require('./pages/HomePage.vue').default,

  },
  {
    name: 'group_select',
    path: '/select_group',
    component: require('./pages/AccountGroupSelectionpage.vue').default
  },
  {
    name: 'not-found',
    path: '*',
    component: require('./pages/NotFoundPage.vue').default,
  },
];

const router = new VueRouter({
  routes,
  linkActiveClass: 'is-active'
});

export default router;
