import VueRouter from 'vue-router';
import store from './store';

const groupSelectedOnly = async (to, from, next) => {
  await store.dispatch('initializeStore');
  
  if (store.state.currentGroup) {
    next();
    return;
  }
  next({name: 'select-account-group'});
};

const routes = [
  {
    name: 'home',
    path: '/',
    component: require('./pages/HomePage.vue').default,
    beforeEnter: groupSelectedOnly
  },
  {
    name: 'upload-data',
    path: '/upload',
    component: require('./pages/UploadDataPage.vue').default
  },
  {
    name: 'transactions-tagging',
    path: '/transaction/tagging',
    component: require('./pages/TagTransactionsPage.vue').default
  },
  {
    name: 'models',
    path: '/models',
    component: require('./pages/ModelsPage.vue').default
  },
  {
    name: 'select-account-group',
    path: '/group/select',
    component: require('./pages/AccountGroupSelectionPage.vue').default
  },
  {
    name: 'create-account-group',
    path: '/group/create',
    component: require('./pages/CreateUpdateAccountGroupPage.vue').default
  },
  {
    name: 'edit-account-group',
    path: '/group/edit/:groupid',
    component: require('./pages/CreateUpdateAccountGroupPage.vue').default
  },
  {
    name: 'merge-accounts',
    path: '/account/merge',
    component: require('./pages/MergeAccountsPage.vue').default  
  },
  {
    name: 'edit-tag-tree',
    path: '/category/tree',
    component: require('./pages/EditTagTreePage.vue').default  
  },
  // {
  //   name: 'edit-account-group',
  //   path: '/group/:groupid/edit',
  //   component: require('./pages/CreateUpdateAccountGroupPage.vue').default
  // },
  {
    name: 'view-account',
    path: '/account/:accountid',
    component: require('./pages/ViewAccountPage.vue').default
  },
  {
    name: 'edit-account',
    path: '/account/:accountid/edit',
    component: require('./pages/EditAccountPage.vue').default
  },
  {
    name: 'help',
    path: '/help',
    component: require('./pages/HelpPage.vue').default
  },
  {
    name: 'not-found',
    path: '*',
    component: require('./pages/NotFoundPage.vue').default,
  }
];

const router = new VueRouter({
  routes,
  linkActiveClass: 'is-active'
});

export default router;
