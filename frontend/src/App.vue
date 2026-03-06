<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppShell from './components/layout/AppShell.vue'
import Toast from 'primevue/toast'

const route = useRoute()
const auth = useAuthStore()

const showShell = computed(() => auth.isAuthenticated && route.name !== 'login')

const cachedViews = [
  'TransactionFlowView',
  'ReviewInboxView',
  'CategoryTransactionsView',
  'ImportDetailView',
  'SwipeTaggerView',
]
</script>

<template>
  <Toast />
  <AppShell v-if="showShell">
    <router-view v-slot="{ Component, route: matchedRoute }">
      <keep-alive :include="cachedViews">
        <component :is="Component" :key="matchedRoute.fullPath" />
      </keep-alive>
    </router-view>
  </AppShell>
  <router-view v-else />
</template>
