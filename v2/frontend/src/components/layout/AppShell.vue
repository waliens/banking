<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'
import { useTransactionStore } from '../../stores/transactions'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const transactionStore = useTransactionStore()
const sidebarCollapsed = ref(false)
const isFullscreen = computed(() => route.path === '/tagger')

const navItems = [
  { label: 'nav.wallet', icon: 'pi pi-home', route: '/' },
  { label: 'nav.review', icon: 'pi pi-inbox', route: '/review', badge: true },
  { label: 'nav.transactions', icon: 'pi pi-list', route: '/transactions' },
  { label: 'nav.import', icon: 'pi pi-upload', route: '/import' },
  { label: 'nav.settings', icon: 'pi pi-cog', route: '/settings' },
]

const mobileNavItems = [
  { label: 'nav.wallet', icon: 'pi pi-home', route: '/' },
  { label: 'nav.tagger', icon: 'pi pi-arrows-h', route: '/tagger', badge: true },
  { label: 'nav.transactions', icon: 'pi pi-list', route: '/transactions' },
  { label: 'nav.import', icon: 'pi pi-upload', route: '/import' },
  { label: 'nav.settings', icon: 'pi pi-cog', route: '/settings' },
]

onMounted(() => {
  transactionStore.fetchReviewCount()
})

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex h-screen">
    <!-- Sidebar (desktop) -->
    <aside
      class="hidden md:flex flex-col bg-surface-900 text-surface-0 transition-all duration-300"
      :class="sidebarCollapsed ? 'w-16' : 'w-56'"
    >
      <div class="flex items-center justify-between p-4">
        <img v-if="!sidebarCollapsed" src="/favicon.svg" alt="Banking Logo" class="h-8 w-8" />
        <span v-if="!sidebarCollapsed" class="text-lg font-bold">Banking</span>
        <button @click="sidebarCollapsed = !sidebarCollapsed" class="p-1 hover:bg-surface-700 rounded">
          <i :class="sidebarCollapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'" />
        </button>
      </div>

      <nav class="flex-1 flex flex-col gap-1 px-2">
        <router-link
          v-for="item in navItems"
          :key="item.route"
          :to="item.route"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-700 transition-colors"
          active-class="bg-surface-700"
        >
          <i :class="item.icon" />
          <span v-if="!sidebarCollapsed" class="flex-1">{{ t(item.label) }}</span>
          <span
            v-if="item.badge && !sidebarCollapsed && transactionStore.reviewCount > 0"
            class="ml-auto bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5 min-w-[20px] text-center"
          >
            {{ transactionStore.reviewCount }}
          </span>
        </router-link>
      </nav>

      <div class="p-2">
        <button
          @click="logout"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-700 transition-colors w-full"
        >
          <i class="pi pi-sign-out" />
          <span v-if="!sidebarCollapsed">{{ t('nav.logout') }}</span>
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main
      class="flex-1 bg-surface-50"
      :class="isFullscreen ? 'overflow-hidden pb-16 md:pb-0' : 'overflow-auto pb-16 md:pb-0'"
    >
      <div :class="isFullscreen ? 'h-full' : 'p-4 md:p-6 max-w-7xl mx-auto'">
        <slot />
      </div>
    </main>

    <!-- Bottom nav (mobile) -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-surface-0 border-t border-surface-200 flex justify-around py-2 z-50">
      <router-link
        v-for="item in mobileNavItems"
        :key="item.route"
        :to="item.route"
        class="relative flex flex-col items-center gap-0.5 px-2 py-1 text-xs text-surface-500"
        active-class="!text-primary-500"
      >
        <i :class="item.icon" class="text-lg" />
        <span>{{ t(item.label) }}</span>
        <span
          v-if="item.badge && transactionStore.reviewCount > 0"
          class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full px-1 min-w-[16px] text-center"
        >
          {{ transactionStore.reviewCount }}
        </span>
      </router-link>
    </nav>
  </div>
</template>
