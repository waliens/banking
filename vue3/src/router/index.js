import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      children: [
        {
          path: '/',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue')
        },
        {
          path: '/users/manage',
          name: 'manage-users',
          component: () => import('@/views/users/ManageUsers.vue'),
          children: [
            {
              path: '/users/manage/create',
              name: 'create-user',
              component: () => import('@/views/users/CreateUser.vue')
            }
          ]
        }
      ],
      meta: { requiresAuth: true } 
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue')
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login');
  } else {
    next();
  }
});

export default router
