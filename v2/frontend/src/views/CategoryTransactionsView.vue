<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import api from '../services/api'
import { useInfiniteScroll } from '../composables/useInfiniteScroll'
import { collapseGroups, isIncome } from '../stores/transactionFlow'
import { useActiveWalletStore } from '../stores/activeWallet'
import FlowTransactionCard from '../components/flow/FlowTransactionCard.vue'
import FlowGroupCard from '../components/flow/FlowGroupCard.vue'
import FlowDetailPanel from '../components/flow/FlowDetailPanel.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const activeWalletStore = useActiveWalletStore()

const walletId = computed(() => route.query.wallet ? Number(route.query.wallet) : null)
const walletAccountIds = computed(() => activeWalletStore.walletAccountIds)
const categoryId = computed(() => route.query.category ? Number(route.query.category) : null)
const dateFrom = computed(() => route.query.date_from || null)
const dateTo = computed(() => route.query.date_to || null)
const categoryName = computed(() => route.query.category_name || t('transactions.uncategorized'))
const periodLabel = computed(() => route.query.period_label || '')

const transactions = ref([])
const groupCache = ref({})
const totalCount = ref(0)
const loading = ref(false)
const PAGE_SIZE = 50

const selectedTx = ref(null)
const drawerVisible = computed({
  get: () => selectedTx.value !== null,
  set: (v) => { if (!v) selectedTx.value = null },
})

function buildParams(start = 0) {
  const params = { start, count: PAGE_SIZE, order: 'desc' }
  if (walletId.value) {
    params.wallet = walletId.value
    params.wallet_external_only = true
  }
  if (categoryId.value) params.category = categoryId.value
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  return params
}

async function fetchGroupDetails(txs) {
  const uncachedGroupIds = [
    ...new Set(
      txs
        .filter((tx) => tx.id_transaction_group && !groupCache.value[tx.id_transaction_group])
        .map((tx) => tx.id_transaction_group),
    ),
  ]
  if (uncachedGroupIds.length > 0 && walletId.value) {
    const groupResults = await Promise.all(
      uncachedGroupIds.map((id) =>
        api.get(`/transaction-groups/${id}`, { params: { wallet_id: walletId.value } }),
      ),
    )
    const newCache = { ...groupCache.value }
    groupResults.forEach((res) => {
      newCache[res.data.id] = res.data
    })
    groupCache.value = newCache
  }
}

async function loadInitial() {
  loading.value = true
  try {
    const params = buildParams(0)
    const [listRes, countRes] = await Promise.all([
      api.get('/transactions', { params }),
      api.get('/transactions/count', { params }),
    ])
    transactions.value = listRes.data
    totalCount.value = countRes.data.count
    await fetchGroupDetails(listRes.data)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || transactions.value.length >= totalCount.value) return
  loading.value = true
  try {
    const params = buildParams(transactions.value.length)
    const { data } = await api.get('/transactions', { params })
    transactions.value.push(...data)
    await fetchGroupDetails(data)
  } finally {
    loading.value = false
  }
}

const hasMore = computed(() => transactions.value.length < totalCount.value)
const sentinel = ref(null)
useInfiniteScroll(sentinel, loadMore, { enabled: hasMore })

// Collapse transactions into groups
const collapsedItems = computed(() => collapseGroups(transactions.value, groupCache.value))

function goBack() {
  router.push({ name: 'wallet', query: { tab: 'table' } })
}

function selectItem(id) {
  selectedTx.value = id
}

onMounted(loadInitial)
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <Button icon="pi pi-arrow-left" :label="t('wallet.backToWallet')" text @click="goBack" />
    </div>

    <h1 class="text-2xl font-bold mb-1">
      {{ t('wallet.categoryTransactions', { category: categoryName }) }}
    </h1>
    <p v-if="periodLabel" class="text-sm text-surface-500 mb-4">{{ periodLabel }}</p>
    <p class="text-sm text-surface-400 mb-4">{{ totalCount }} {{ t('transactions.title').toLowerCase() }}</p>

    <div v-if="collapsedItems.length" class="space-y-2">
      <div
        v-for="item in collapsedItems"
        :key="item.type === 'group' ? `group-${item.group.id}` : `tx-${item.transaction.id}`"
      >
        <FlowGroupCard
          v-if="item.type === 'group'"
          :group="item.group"
          :direction="Number(item.group.net_expense) <= 0 ? 'income' : 'expense'"
          @select="selectItem"
        />
        <FlowTransactionCard
          v-else
          :transaction="item.transaction"
          :direction="isIncome(item.transaction, 'wallet', walletId, walletAccountIds) ? 'income' : 'expense'"
          @select="selectItem"
        />
      </div>
      <div ref="sentinel" class="h-4" />
      <p v-if="loading" class="text-center text-surface-400 py-2">{{ t('common.loading') }}</p>
    </div>

    <p v-else-if="!loading" class="text-surface-500 text-center py-8">{{ t('flow.noTransactions') }}</p>
    <p v-else class="text-surface-500 text-center py-8">{{ t('common.loading') }}</p>

    <Drawer v-model:visible="drawerVisible" position="right" :header="t('flow.transactionDetail')" :style="{ width: '36rem' }">
      <FlowDetailPanel
        v-if="selectedTx"
        :transactionId="selectedTx"
        @back="selectedTx = null"
      />
    </Drawer>
  </div>
</template>
