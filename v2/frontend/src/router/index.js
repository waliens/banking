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
    name: 'wallet',
    component: () => import('../views/WalletTabView.vue'),
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('../views/ReviewInboxView.vue'),
  },
  {
    path: '/transactions',
    name: 'transactions',
    component: () => import('../views/TransactionFlowView.vue'),
  },
  {
    path: '/transactions/:id',
    name: 'transaction-detail',
    component: () => import('../views/TransactionDetailView.vue'),
  },
  {
    path: '/import',
    name: 'import',
    component: () => import('../views/ImportView.vue'),
  },
  {
    path: '/imports/:id',
    name: 'import-detail',
    component: () => import('../views/ImportDetailView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/tagger',
    name: 'tagger',
    component: () => import('../views/SwipeTaggerView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let activeWalletInitialized = false

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // try to restore session
  if (!auth.user && auth.token) {
    await auth.fetchUser()
  }

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login' }
  }

  // Initialize active wallet once after session restore
  if (auth.isAuthenticated && !activeWalletInitialized) {
    activeWalletInitialized = true
    const { useActiveWalletStore } = await import('../stores/activeWallet')
    const activeWalletStore = useActiveWalletStore()
    await activeWalletStore.initialize(auth.user)
  }
})

export default router
