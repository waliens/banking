<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useTransactionStore } from '../stores/transactions'
import { useCategoryStore } from '../stores/categories'
import { useMLStore } from '../stores/ml'
import { useActiveWalletStore } from '../stores/activeWallet'
import { useSwipeGesture } from '../composables/useSwipeGesture'
import { usePanelSwipeBack } from '../composables/usePanelSwipeBack'
import CategoryGrid from '../components/tagger/CategoryGrid.vue'
import MLSuggestion from '../components/MLSuggestion.vue'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'
import AccountDisplay from '../components/common/AccountDisplay.vue'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import TransactionGroupDetail from '../components/transactions/TransactionGroupDetail.vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

defineOptions({ name: 'SwipeTaggerView' })

const { t } = useI18n()
const router = useRouter()
const transactionStore = useTransactionStore()
const categoryStore = useCategoryStore()
const mlStore = useMLStore()
const activeWalletStore = useActiveWalletStore()

const mode = ref('card') // 'card' | 'pick-parent' | 'pick-child' | 'detail'
const currentIndex = ref(0)
const processedCount = ref(0)
const selectedParent = ref(null)
const animatingOut = ref(null) // 'left' | 'right' | 'up' | 'down' | null
const cardRef = ref(null)

// Panel refs for swipe-to-go-back
const parentPanelRef = ref(null)
const childPanelRef = ref(null)
const detailPanelRef = ref(null)

const batch = ref([]) // mixed: { type: 'transaction', data: tx } or { type: 'group', data: group }
const allDone = ref(false)

const currentItem = computed(() => batch.value[currentIndex.value] || null)
const currentTx = computed(() => currentItem.value?.type === 'transaction' ? currentItem.value.data : null)
const currentGroup = computed(() => currentItem.value?.type === 'group' ? currentItem.value.data : null)
const isGroup = computed(() => currentItem.value?.type === 'group')
const currentPrediction = computed(() => currentTx.value ? mlStore.predictions[currentTx.value.id] : null)

const parentCategories = computed(() => categoryStore.categoryTree)
const childCategories = computed(() => {
  if (!selectedParent.value) return []
  const parent = categoryStore.categoryTree.find(c => c.id === selectedParent.value)
  return parent ? parent.children : []
})

// Card swipe gesture (only for card mode)
const { offsetX, offsetY, swipeDirection } = useSwipeGesture(cardRef, {
  onSwipeRight: handleSwipeRight,
  onSwipeLeft: handleSwipeLeft,
  onSwipeUp: handleSwipeUp,
  onSwipeDown: handleSwipeDown,
  threshold: 100,
})

// Panel swipe-back gestures
usePanelSwipeBack(parentPanelRef, { onBack: backToCard, direction: 'right' })
usePanelSwipeBack(childPanelRef, { onBack: backToParent, direction: 'right' })
usePanelSwipeBack(detailPanelRef, { onBack: backToCard, direction: 'up' })

const cardTransform = computed(() => {
  if (animatingOut.value) return undefined
  return `translateX(${offsetX.value}px) translateY(${offsetY.value}px) rotate(${offsetX.value * 0.05}deg)`
})

const cardOpacity = computed(() => {
  if (animatingOut.value) return 0
  return 1 - Math.max(Math.abs(offsetX.value), Math.abs(offsetY.value)) / 600
})

const overlayClass = computed(() => {
  if (swipeDirection.value === 'right' && (currentPrediction.value || isGroup.value)) return 'border-green-500'
  if (swipeDirection.value === 'up') return 'border-surface-400'
  if (swipeDirection.value === 'left') return 'border-indigo-500'
  if (swipeDirection.value === 'down') return 'border-blue-500'
  return 'border-transparent'
})

const overlayLabel = computed(() => {
  if (swipeDirection.value === 'right' && currentPrediction.value) return currentPrediction.value.category_name
  if (swipeDirection.value === 'up') return t('tagger.skip')
  if (swipeDirection.value === 'left') return t('tagger.categorize')
  if (swipeDirection.value === 'down') return t('tagger.detail')
  return ''
})

// Title for current mode (shown next to back button in header)
const modeTitle = computed(() => {
  if (mode.value === 'pick-child') return t('tagger.pickSubCategory')
  if (mode.value === 'pick-parent') return t('tagger.pickCategory')
  if (mode.value === 'detail') return t('tagger.detail')
  return ''
})

// Wallet-relative display amount for current item
const displayAmount = computed(() => {
  if (isGroup.value && currentGroup.value) {
    // For groups, net_expense is already the wallet-relative amount (positive = expense)
    return -currentGroup.value.net_expense
  }
  if (currentTx.value) {
    // Negate for expenses (wallet account is source), keep positive for income
    if (isWalletAccount(currentTx.value.dest)) return currentTx.value.amount
    return -currentTx.value.amount
  }
  return 0
})

const displayCurrency = computed(() => {
  if (currentTx.value) return currentTx.value.currency?.symbol || ''
  if (currentGroup.value && currentGroup.value.transactions?.length > 0) {
    return currentGroup.value.transactions[0].currency?.symbol || ''
  }
  return ''
})

function isWalletAccount(account) {
  if (!account) return false
  return activeWalletStore.walletAccountIds.includes(account.id)
}

async function loadBatch() {
  const walletId = activeWalletStore.activeWalletId

  const txParams = {
    is_reviewed: false,
    labeled: false,
    duplicate_only: false,
    exclude_grouped: true,
    start: 0,
    count: 20,
    order: 'desc',
  }

  if (walletId) {
    txParams.wallet = walletId
    txParams.wallet_external_only = true
  }

  // Load transactions and groups in parallel
  const groupsPromise = walletId
    ? transactionStore.fetchUnreviewedGroups(walletId)
    : Promise.resolve([])

  const [, groups] = await Promise.all([
    transactionStore.fetchTransactions(txParams),
    groupsPromise,
  ])
  const txItems = transactionStore.transactions.map(tx => ({ type: 'transaction', data: tx }))
  const groupItems = (groups || []).map(g => ({ type: 'group', data: g }))

  // Merge: groups first, then transactions (both by date desc)
  batch.value = [...groupItems, ...txItems]
  currentIndex.value = 0

  if (batch.value.length === 0) {
    allDone.value = true
    return
  }

  // ML predictions for transactions only
  const txIds = txItems.map(item => item.data.id)
  if (txIds.length > 0) {
    try {
      await mlStore.predictTransactions(txIds)
    } catch {
      // ML predictions optional
    }
  }
}

async function animateAndAdvance(direction) {
  animatingOut.value = direction
  await new Promise(r => setTimeout(r, 300))
  animatingOut.value = null
  processedCount.value++
  currentIndex.value++

  if (currentIndex.value >= batch.value.length) {
    await loadBatch()
    if (batch.value.length === 0) {
      allDone.value = true
    }
  }

  await nextTick()
  mode.value = 'card'
}

async function handleSwipeRight() {
  if (!currentItem.value) return
  if (isGroup.value) {
    // No ML prediction for groups, right swipe does nothing
    return
  }
  if (!currentPrediction.value) return
  await transactionStore.setCategory(currentTx.value.id, currentPrediction.value.category_id)
  await transactionStore.fetchReviewCount()
  animateAndAdvance('right')
}

async function handleSwipeUp() {
  if (!currentItem.value) return
  if (isGroup.value) {
    const walletId = activeWalletStore.activeWalletId
    if (walletId) await transactionStore.reviewGroup(currentGroup.value.id, walletId)
  } else {
    await transactionStore.reviewTransaction(currentTx.value.id)
  }
  await transactionStore.fetchReviewCount()
  animateAndAdvance('up')
}

function handleSwipeLeft() {
  if (!currentItem.value) return
  mode.value = 'pick-parent'
}

function handleSwipeDown() {
  if (!currentItem.value) return
  mode.value = 'detail'
}

function openFullDetail() {
  if (isGroup.value) {
    router.push(`/groups/${currentItem.value.data.id}`)
  } else {
    router.push(`/transactions/${currentItem.value.data.id}`)
  }
}

async function onDetailCategoryChanged() {
  await transactionStore.fetchReviewCount()
  selectedParent.value = null
  animateAndAdvance('down')
}

async function selectParent(categoryId) {
  const parent = categoryStore.categoryTree.find(c => c.id === categoryId)
  if (parent && parent.children.length > 0) {
    selectedParent.value = categoryId
    mode.value = 'pick-child'
  } else {
    await applyCategory(categoryId)
  }
}

async function selectChild(categoryId) {
  await applyCategory(categoryId)
}

async function applyCategory(categoryId) {
  if (!currentItem.value) return
  if (isGroup.value) {
    const walletId = activeWalletStore.activeWalletId
    if (walletId) await transactionStore.setGroupCategory(currentGroup.value.id, categoryId, walletId)
  } else {
    await transactionStore.setCategory(currentTx.value.id, categoryId)
  }
  await transactionStore.fetchReviewCount()
  selectedParent.value = null
  animateAndAdvance('left')
}

function handleBack() {
  if (mode.value === 'pick-child') {
    backToParent()
  } else {
    backToCard()
  }
}

function backToCard() {
  mode.value = 'card'
  selectedParent.value = null
}

function backToParent() {
  mode.value = 'pick-parent'
  selectedParent.value = null
}

// Description for the current item
const itemDescription = computed(() => {
  if (isGroup.value && currentGroup.value) {
    return currentGroup.value.name || t('tagger.group')
  }
  if (currentTx.value) return currentTx.value.description || '—'
  return '—'
})

const itemDate = computed(() => {
  if (isGroup.value && currentGroup.value && currentGroup.value.transactions?.length > 0) {
    // Use date of most recent transaction in group
    const dates = currentGroup.value.transactions.map(tx => tx.date).sort()
    return dates[dates.length - 1]
  }
  if (currentTx.value) return currentTx.value.date
  return ''
})

const itemAccount = computed(() => {
  if (currentTx.value?.source) return currentTx.value.source.name || currentTx.value.source.number
  return null
})

onMounted(async () => {
  await Promise.all([loadBatch(), categoryStore.fetchCategories()])
})
</script>

<template>
  <div class="h-full bg-surface-50 flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-surface-0 border-b border-surface-200">
      <!-- Back button + section title (in top bar when not in card mode) -->
      <button v-if="mode !== 'card'" @click="handleBack" class="text-primary-500 flex items-center gap-2">
        <i class="pi pi-arrow-left text-sm" />
        <span class="text-sm font-bold text-surface-800">{{ modeTitle }}</span>
      </button>
      <div v-else></div>

      <span class="text-sm text-surface-500">
        {{ processedCount }} {{ t('tagger.processed') }} &middot; {{ transactionStore.reviewCount }} {{ t('tagger.remaining') }}
      </span>
    </div>

    <!-- Main content area -->
    <div class="flex-1 min-h-0">
      <!-- All done state -->
      <div v-if="allDone" class="h-full flex items-center justify-center p-4">
        <div class="text-center">
          <i class="pi pi-check-circle text-5xl text-green-500 mb-4 block" />
          <h2 class="text-xl font-bold mb-2">{{ t('tagger.allDone') }}</h2>
          <p class="text-surface-500">{{ t('tagger.allDoneDesc') }}</p>
        </div>
      </div>

      <!-- Card mode (non-scrollable, centered) -->
      <div v-else-if="mode === 'card' && currentItem" class="h-full flex items-center justify-center p-4">
        <div class="w-full max-w-sm">
          <div
            ref="cardRef"
            class="bg-surface-0 rounded-2xl shadow-lg p-6 border-4 transition-all select-none touch-none"
            :class="overlayClass"
            :style="{
              transform: cardTransform,
              opacity: cardOpacity,
              transition: animatingOut ? 'transform 0.3s ease-out, opacity 0.3s ease-out' : 'none',
            }"
          >
            <!-- Overlay label -->
            <div
              v-if="overlayLabel"
              class="text-center text-sm font-bold mb-3 uppercase tracking-wide"
              :class="{
                'text-green-600': swipeDirection === 'right',
                'text-surface-400': swipeDirection === 'up',
                'text-indigo-600': swipeDirection === 'left',
                'text-blue-600': swipeDirection === 'down',
              }"
            >
              {{ overlayLabel }}
            </div>

            <!-- Group badge -->
            <div v-if="isGroup" class="flex justify-center mb-3">
              <Tag :value="t('tagger.group')" severity="info" icon="pi pi-link" />
            </div>

            <!-- Amount (wallet-relative) -->
            <div class="text-3xl font-bold text-center mb-4">
              <CurrencyDisplay
                :amount="displayAmount"
                :currencySymbol="displayCurrency"
                :showSign="true"
                colored
              />
            </div>

            <!-- Group details -->
            <div v-if="isGroup && currentGroup" class="text-center text-xs text-surface-400 -mt-2 mb-4">
              {{ t('tagger.groupNetExpense') }}: {{ currentGroup.net_expense }}
              &middot; {{ t('tagger.groupTransactions', { count: currentGroup.transactions?.length || 0 }) }}
            </div>

            <!-- Effective amount for transactions -->
            <div
              v-if="!isGroup && currentTx && currentTx.effective_amount != null && currentTx.effective_amount !== currentTx.amount"
              class="text-center text-sm text-surface-400 -mt-2 mb-4"
            >
              {{ t('transactions.effectiveAmount') }}: {{ currentTx.effective_amount }}
            </div>

            <!-- Description -->
            <div class="text-center text-surface-700 font-medium mb-2 truncate">
              {{ itemDescription }}
            </div>

            <!-- Date & Account -->
            <div class="text-center text-sm text-surface-400 mb-4">
              {{ itemDate }}
              <span v-if="itemAccount"> &middot; {{ itemAccount }}</span>
            </div>

            <!-- ML Suggestion (transactions only) -->
            <div v-if="!isGroup" class="flex justify-center">
              <div v-if="currentPrediction" class="text-center">
                <MLSuggestion
                  :categoryName="currentPrediction.category_name"
                  :categoryColor="currentPrediction.category_color"
                  :probability="currentPrediction.probability"
                  @accept="handleSwipeRight"
                />
                <p class="text-xs text-surface-400 mt-2">{{ t('tagger.swipeRightToAccept') }}</p>
              </div>
              <p v-else class="text-xs text-surface-400">{{ t('tagger.hintLeft') }} ←</p>
            </div>

            <!-- Group: just show categorize hint -->
            <div v-else class="flex justify-center">
              <p class="text-xs text-surface-400">{{ t('tagger.hintLeft') }} ←</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Pick parent category (scrollable, swipe right to dismiss) -->
      <div v-else-if="mode === 'pick-parent'" ref="parentPanelRef" class="h-full overflow-y-auto p-4">
        <div class="max-w-lg mx-auto">
          <CategoryGrid :categories="parentCategories" :transaction="currentTx || currentGroup" @select="selectParent" />
        </div>
      </div>

      <!-- Pick child category (scrollable, swipe right to dismiss) -->
      <div v-else-if="mode === 'pick-child'" ref="childPanelRef" class="h-full overflow-y-auto p-4">
        <div class="max-w-lg mx-auto">
          <CategoryGrid :categories="childCategories" :transaction="currentTx || currentGroup" @select="selectChild" />
        </div>
      </div>

      <!-- Detail mode (scrollable, pull down at top to dismiss) -->
      <div v-else-if="mode === 'detail'" ref="detailPanelRef" class="h-full overflow-y-auto p-4">
        <div class="max-w-lg mx-auto">
          <template v-if="currentTx">
            <div class="bg-surface-0 rounded-xl shadow p-4">
              <TransactionDetail :transaction="currentTx" @categoryChanged="onDetailCategoryChanged" />
            </div>
          </template>
          <template v-else-if="currentGroup">
            <div class="bg-surface-0 rounded-xl shadow p-4">
              <TransactionGroupDetail :group="currentGroup" />
            </div>
          </template>
          <div class="mt-4 text-center">
            <Button
              :label="t('transactionDetail.openFullPage')"
              icon="pi pi-external-link"
              severity="secondary"
              size="small"
              text
              @click="openFullDetail"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom hints bar (card mode only) -->
    <div v-if="!allDone && mode === 'card'" class="bg-surface-0 border-t border-surface-200 py-3 px-4">
      <div class="flex justify-between text-xs text-surface-400 max-w-sm mx-auto">
        <span>← {{ t('tagger.hintLeft') }}</span>
        <span>↑ {{ t('tagger.hintUp') }}</span>
        <span>↓ {{ t('tagger.hintDown') }}</span>
        <span v-if="currentPrediction">{{ t('tagger.hintRight') }} →</span>
      </div>
    </div>
  </div>
</template>
