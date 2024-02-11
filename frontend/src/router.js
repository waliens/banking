import VueRouter from 'vue-router';
import store from './store';

const groupSelectedOnly = async (to, from, next) => {
  await store.dispatch('initializeStore');
  if (store.state.currentUser != null && store.state.currentGroup) {
    next();
    return;
  }
  next({name: 'select-account-group'});
};

const authenticatedOnly = async (to, from, next) => {
  await store.dispatch('initializeStore');
  if (store.state.currentUser != null) {
    next();
    return;
  }
  next({name: 'login', query: {next: to.fullPath}});
};

const notAuthenticatedOnly = async (to, from, next) => {
  await store.dispatch('initializeStore');

  if (store.state.currentUser == null) {
    next();
    return;
  }

  next({name: 'dashboard', query: {next: to.fullPath}});
}


const routes = [
  {
    path: '/',
    component: require('./pages/DashboardPage.vue').default,
    beforeEnter: groupSelectedOnly
  },
  {
    path: '/test',
    component: require('./pages/TestPage.vue').default,
  },
  {
    name: 'login',
    path: '/login',
    component: require('./pages/LoginPage.vue').default,
    beforeEnter: notAuthenticatedOnly
  },
  {
    name: 'dashboard',
    path: '/dashboard',
    component: require('./pages/DashboardPage.vue').default,
    beforeEnter: groupSelectedOnly
  },
  {
    name: 'upload-data',
    path: '/upload',
    component: require('./pages/UploadDataPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'transactions-tagging',
    path: '/transaction/tagging',
    component: require('./pages/TagTransactionsPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'models',
    path: '/models',
    component: require('./pages/ModelsPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'select-account-group',
    path: '/group/select',
    component: require('./pages/AccountGroupSelectionPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'create-account-group',
    path: '/group/create',
    component: require('./pages/CreateUpdateAccountGroupPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'edit-account-group',
    path: '/group/edit/:groupid',
    component: require('./pages/CreateUpdateAccountGroupPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'create-transaction',
    path: '/transaction',
    component: require('./pages/CreateUpdateManualTransactionPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'edit-transaction',
    path: '/transaction/:transactionid',
    component: require('./pages/CreateUpdateManualTransactionPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'manage-duplicate-transactions',
    path: '/duplicates',
    component: require('./pages/DuplicateTransactionManagementPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'merge-accounts',
    path: '/account/merge',
    component: require('./pages/MergeAccountsPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'edit-tag-tree',
    path: '/category/tree',
    component: require('./pages/EditTagTreePage.vue').default,
    beforeEnter: authenticatedOnly
  },
  // {
  //   name: 'edit-account-group',
  //   path: '/group/:groupid/edit',
  //   component: require('./pages/CreateUpdateAccountGroupPage.vue').default
  // },
  {
    name: 'view-account',
    path: '/account/:accountid',
    component: require('./pages/ViewAccountPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'edit-account',
    path: '/account/:accountid/edit',
    component: require('./pages/EditAccountPage.vue').default,
    beforeEnter: authenticatedOnly
  },
  {
    name: 'manage-users',
    path: '/users/manage',
    component: require('./pages/ManageUsersPage.vue').default,
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
