import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // {
    //   path: '/',
    //   component: LoggedLayout,
    //   children: [
    //     {
    //       path: '/',
    //       name: 'dashboard',
    //       component: () => import('@/views/Dashboard.vue')
    //     }
    //   ]
    // },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue')
    }
  ]
})

export default router
