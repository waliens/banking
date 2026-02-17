<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTransactionStore } from '../stores/transactions'
import { useCategoryStore } from '../stores/categories'
import { useMLStore } from '../stores/ml'
import { useActiveWalletStore } from '../stores/activeWallet'
import { useSwipeGesture } from '../composables/useSwipeGesture'
import CategoryGrid from '../components/tagger/CategoryGrid.vue'
import MLSuggestion from '../components/MLSuggestion.vue'
import TransactionDetail from '../components/transactions/TransactionDetail.vue'
import Button from 'primevue/button'
import CurrencyDisplay from '../components/common/CurrencyDisplay.vue'

const { t } = useI18n()
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

const batch = ref([])
const allDone = ref(false)

const currentTx = computed(() => batch.value[currentIndex.value] || null)
const currentPrediction = computed(() => currentTx.value ? mlStore.predictions[currentTx.value.id] : null)
const remaining = computed(() => batch.value.length - currentIndex.value)

const parentCategories = computed(() => categoryStore.categoryTree)
const childCategories = computed(() => {
  if (!selectedParent.value) return []
  const parent = categoryStore.categoryTree.find(c => c.id === selectedParent.value)
  return parent ? parent.children : []
})

const { offsetX, offsetY, swipeDirection } = useSwipeGesture(cardRef, {
  onSwipeRight: handleSwipeRight,
  onSwipeLeft: handleSwipeLeft,
  onSwipeUp: handleSwipeUp,
  onSwipeDown: handleSwipeDown,
  threshold: 100,
})

const cardTransform = computed(() => {
  if (animatingOut.value) return undefined // CSS transition handles it
  return `translateX(${offsetX.value}px) translateY(${offsetY.value}px) rotate(${offsetX.value * 0.05}deg)`
})

const cardOpacity = computed(() => {
  if (animatingOut.value) return 0
  return 1 - Math.max(Math.abs(offsetX.value), Math.abs(offsetY.value)) / 600
})

const overlayClass = computed(() => {
  if (swipeDirection.value === 'right' && currentPrediction.value) return 'border-green-500'
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

async function loadBatch() {
  const params = {
    is_reviewed: false,
    labeled: false,
    duplicate_only: false,
    start: 0,
    count: 20,
    order: 'desc',
  }

  // Wallet scoping
  const walletId = activeWalletStore.activeWalletId
  if (walletId) {
    params.wallet = walletId
    params.wallet_external_only = true
  }

  await transactionStore.fetchTransactions(params)
  batch.value = [...transactionStore.transactions]
  currentIndex.value = 0

  if (batch.value.length === 0) {
    allDone.value = true
    return
  }

  const ids = batch.value.map(t => t.id)
  try {
    await mlStore.predictTransactions(ids)
  } catch {
    // ML predictions optional
  }
}

async function animateAndAdvance(direction) {
  animatingOut.value = direction
  await new Promise(r => setTimeout(r, 300))
  animatingOut.value = null
  processedCount.value++
  currentIndex.value++

  if (currentIndex.value >= batch.value.length) {
    // Try to load more
    await loadBatch()
    if (batch.value.length === 0) {
      allDone.value = true
    }
  }

  await nextTick()
  mode.value = 'card'
}

async function handleSwipeRight() {
  if (!currentPrediction.value || !currentTx.value) return
  await transactionStore.setCategory(currentTx.value.id, currentPrediction.value.category_id)
  await transactionStore.fetchReviewCount()
  animateAndAdvance('right')
}

async function handleSwipeUp() {
  if (!currentTx.value) return
  await transactionStore.reviewTransaction(currentTx.value.id)
  await transactionStore.fetchReviewCount()
  animateAndAdvance('up')
}

function handleSwipeLeft() {
  if (!currentTx.value) return
  mode.value = 'pick-parent'
}

function handleSwipeDown() {
  if (!currentTx.value) return
  mode.value = 'detail'
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
  if (!currentTx.value) return
  await transactionStore.setCategory(currentTx.value.id, categoryId)
  await transactionStore.fetchReviewCount()
  selectedParent.value = null
  animateAndAdvance('left')
}

function backToCard() {
  mode.value = 'card'
  selectedParent.value = null
}

function backToParent() {
  mode.value = 'pick-parent'
  selectedParent.value = null
}

onMounted(async () => {
  await Promise.all([loadBatch(), categoryStore.fetchCategories()])
})
</script>

<template>
  <div class="h-full bg-surface-50 flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-surface-0 border-b border-surface-200">
      <router-link to="/review" class="text-primary-500 flex items-center gap-1">
        <i class="pi pi-arrow-left text-sm" />
        <span>{{ t('tagger.back') }}</span>
      </router-link>
      <span class="text-sm text-surface-500">
        {{ processedCount }} {{ t('tagger.processed') }} / {{ remaining }} remaining
      </span>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col items-center justify-center p-4 min-h-0 overflow-y-auto">
      <!-- All done state -->
      <div v-if="allDone" class="text-center">
        <i class="pi pi-check-circle text-5xl text-green-500 mb-4 block" />
        <h2 class="text-xl font-bold mb-2">{{ t('tagger.allDone') }}</h2>
        <p class="text-surface-500 mb-6">{{ t('tagger.allDoneDesc') }}</p>
        <router-link to="/review">
          <Button :label="t('tagger.backToReview')" icon="pi pi-arrow-left" />
        </router-link>
      </div>

      <!-- Card mode -->
      <div v-else-if="mode === 'card' && currentTx" class="w-full max-w-sm">
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

          <!-- Amount -->
          <div class="text-3xl font-bold text-center mb-4">
            <CurrencyDisplay
              :amount="currentTx.amount"
              :currencySymbol="currentTx.currency_symbol || ''"
              :showSign="true"
              colored
            />
          </div>
          <div
            v-if="currentTx.effective_amount != null && currentTx.effective_amount !== currentTx.amount"
            class="text-center text-sm text-surface-400 -mt-2 mb-4"
          >
            {{ t('transactions.effectiveAmount') }}: {{ currentTx.effective_amount }}
          </div>

          <!-- Description -->
          <div class="text-center text-surface-700 font-medium mb-2 truncate">
            {{ currentTx.description || '—' }}
          </div>

          <!-- Date & Account -->
          <div class="text-center text-sm text-surface-400 mb-4">
            {{ currentTx.date }}
            <span v-if="currentTx.source"> &middot; {{ currentTx.source.name || currentTx.source.number }}</span>
          </div>

          <!-- ML Suggestion -->
          <div class="flex justify-center">
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
        </div>
      </div>

      <!-- Detail mode -->
      <div v-else-if="mode === 'detail' && currentTx" class="w-full max-w-lg">
        <div class="flex items-center gap-2 mb-4">
          <button @click="backToCard" class="text-primary-500">
            <i class="pi pi-arrow-left" />
          </button>
          <h3 class="font-bold">{{ t('tagger.detail') }}</h3>
        </div>
        <div class="bg-surface-0 rounded-xl shadow p-4">
          <TransactionDetail :transaction="currentTx" @categoryChanged="backToCard" />
        </div>
      </div>

      <!-- Pick parent category -->
      <div v-else-if="mode === 'pick-parent'" class="w-full max-w-lg">
        <div class="flex items-center gap-2 mb-4">
          <button @click="backToCard" class="text-primary-500">
            <i class="pi pi-arrow-left" />
          </button>
          <h3 class="font-bold">{{ t('tagger.pickCategory') }}</h3>
        </div>
        <CategoryGrid :categories="parentCategories" :transaction="currentTx" @select="selectParent" />
      </div>

      <!-- Pick child category -->
      <div v-else-if="mode === 'pick-child'" class="w-full max-w-lg">
        <div class="flex items-center gap-2 mb-4">
          <button @click="backToParent" class="text-primary-500">
            <i class="pi pi-arrow-left" />
          </button>
          <h3 class="font-bold">{{ t('tagger.pickSubCategory') }}</h3>
        </div>
        <CategoryGrid :categories="childCategories" :transaction="currentTx" @select="selectChild" />
      </div>
    </div>

    <!-- Bottom hints bar (card mode only) -->
    <div v-if="!allDone && mode === 'card'" class="bg-surface-0 border-t border-surface-200 py-3 px-4">
      <div class="flex justify-between text-xs text-surface-400 max-w-sm mx-auto">
        <span>← {{ t('tagger.hintLeft') }}</span>
        <span>↑ {{ t('tagger.hintUp') }}</span>
        <span>↓ {{ t('tagger.hintDown') }}</span>
        <span>{{ t('tagger.hintRight') }} →</span>
      </div>
    </div>
  </div>
</template>
