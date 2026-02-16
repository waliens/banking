import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('../views/ReviewInboxView.vue'),
  },
  {
    path: '/transactions',
    name: 'transactions',
    component: () => import('../views/TransactionsView.vue'),
  },
  {
    path: '/accounts',
    name: 'accounts',
    component: () => import('../views/AccountsView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/wallets',
    name: 'wallets',
    component: () => import('../views/WalletsView.vue'),
  },
  {
    path: '/wallets/:id',
    name: 'wallet-detail',
    component: () => import('../views/WalletDetailView.vue'),
  },
  {
    path: '/import',
    name: 'import',
    component: () => import('../views/ImportView.vue'),
  },
  {
    path: '/tagger',
    name: 'tagger',
    component: () => import('../views/SwipeTaggerView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // try to restore session
  if (!auth.user && auth.token) {
    await auth.fetchUser()
  }

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router
