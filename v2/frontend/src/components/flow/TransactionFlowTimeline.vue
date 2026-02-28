<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SelectButton from 'primevue/selectbutton'
import InputText from 'primevue/inputtext'
import { useTransactionFlowStore, isIncome, collapseGroups } from '../../stores/transactionFlow'
import { useInfiniteScroll } from '../../composables/useInfiniteScroll'
import FlowTransactionCard from './FlowTransactionCard.vue'
import FlowGroupCard from './FlowGroupCard.vue'
import FlowDateSeparator from './FlowDateSeparator.vue'

const { t } = useI18n()
const flowStore = useTransactionFlowStore()

const props = defineProps({
  contextType: { type: String, required: true },
  contextId: { type: Number, required: true },
  walletAccountIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['select'])

const periodMode = ref('month')
const periodOptions = computed(() => [
  { label: t('flow.month'), value: 'month' },
  { label: t('flow.day'), value: 'day' },
])

const searchQuery = ref('')
let searchTimeout = null

function onSearchInput(val) {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchQuery.value = val
  }, 300)
}

function buildParams() {
  const params = { wallet_external_only: true }
  if (props.contextType === 'wallet') {
    params.wallet = props.contextId
  } else {
    params.account = props.contextId
  }
  if (searchQuery.value) {
    params.search_query = searchQuery.value
  }
  return params
}

function loadMore() {
  flowStore.fetchPage(buildParams())
}

// Reset on context or search change
watch([() => props.contextId, () => props.contextType, searchQuery], () => {
  flowStore.reset()
  loadMore()
})

// Initial load
flowStore.reset()
loadMore()

// Period grouping
function periodKey(dateStr) {
  if (!dateStr) return 'unknown'
  const parts = dateStr.split('-')
  if (periodMode.value === 'month') {
    return `${parts[0]}-${parts[1]}`
  }
  return dateStr
}

function periodLabel(key) {
  if (key === 'unknown') return ''
  const parts = key.split('-')
  if (periodMode.value === 'month') {
    const date = new Date(Number(parts[0]), Number(parts[1]) - 1)
    return date.toLocaleDateString('en', { month: 'long', year: 'numeric' })
  }
  const date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
  return date.toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

const groupedByPeriod = computed(() => {
  const collapsed = collapseGroups(flowStore.items, flowStore.groupCache)
  const map = new Map()

  for (const item of collapsed) {
    const key = periodKey(item.date)
    if (!map.has(key)) {
      map.set(key, { label: periodLabel(key), income: [], expense: [] })
    }
    const entry = map.get(key)

    let itemIsIncome
    if (item.type === 'group') {
      // Positive net_expense = expense, zero/negative = income
      itemIsIncome = Number(item.group.net_expense) <= 0
    } else {
      itemIsIncome = isIncome(item.transaction, props.contextType, props.contextId, props.walletAccountIds)
    }

    if (itemIsIncome) {
      entry.income.push(item)
    } else {
      entry.expense.push(item)
    }
  }

  return map
})

// Infinite scroll
const sentinelRef = ref(null)
const scrollEnabled = computed(() => flowStore.hasMore && !flowStore.loading)
useInfiniteScroll(sentinelRef, loadMore, { enabled: scrollEnabled })

// Period mode change regroups but doesn't refetch
watch(periodMode, () => {
  // groupedByPeriod is computed, so it recomputes automatically
})
</script>

<template>
  <div>
    <!-- Controls -->
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium">{{ t('flow.groupBy') }}:</span>
        <SelectButton
          v-model="periodMode"
          :options="periodOptions"
          optionLabel="label"
          optionValue="value"
          :allowEmpty="false"
        />
      </div>
      <div class="flex-1 min-w-48 max-w-sm">
        <InputText
          :placeholder="t('common.search')"
          class="w-full"
          @input="onSearchInput($event.target.value)"
        />
      </div>
    </div>

    <!-- Desktop timeline -->
    <div class="hidden md:block">
      <template v-for="[key, period] of groupedByPeriod" :key="key">
        <div class="grid grid-cols-[1fr_2rem_1fr] gap-y-2">
          <FlowDateSeparator :label="period.label" />

          <!-- Interleave income (left) and expense (right) -->
          <template
            v-for="(_, idx) in Math.max(period.income.length, period.expense.length)"
            :key="idx"
          >
            <!-- Left (income) -->
            <div class="flex justify-end">
              <div v-if="period.income[idx]" class="w-full max-w-sm">
                <FlowGroupCard
                  v-if="period.income[idx].type === 'group'"
                  :group="period.income[idx].group"
                  direction="income"
                  @select="(id) => emit('select', id)"
                />
                <FlowTransactionCard
                  v-else
                  :transaction="period.income[idx].transaction"
                  direction="income"
                  @select="(id) => emit('select', id)"
                />
              </div>
            </div>

            <!-- Center timeline -->
            <div class="flex justify-center">
              <div class="w-0.5 bg-primary-100 h-full min-h-[3rem]"></div>
            </div>

            <!-- Right (expense) -->
            <div>
              <div v-if="period.expense[idx]" class="w-full max-w-sm">
                <FlowGroupCard
                  v-if="period.expense[idx].type === 'group'"
                  :group="period.expense[idx].group"
                  direction="expense"
                  @select="(id) => emit('select', id)"
                />
                <FlowTransactionCard
                  v-else
                  :transaction="period.expense[idx].transaction"
                  direction="expense"
                  @select="(id) => emit('select', id)"
                />
              </div>
            </div>
          </template>
        </div>
      </template>
    </div>

    <!-- Mobile layout -->
    <div class="md:hidden space-y-2">
      <template v-for="[key, period] of groupedByPeriod" :key="key">
        <FlowDateSeparator :label="period.label" />

        <template v-for="item in [...period.income, ...period.expense]" :key="item.group?.id || item.transaction?.id">
          <FlowGroupCard
            v-if="item.type === 'group'"
            :group="item.group"
            :direction="period.income.includes(item) ? 'income' : 'expense'"
            :mobile="true"
            @select="(id) => emit('select', id)"
          />
          <FlowTransactionCard
            v-else
            :transaction="item.transaction"
            :direction="period.income.includes(item) ? 'income' : 'expense'"
            :mobile="true"
            @select="(id) => emit('select', id)"
          />
        </template>
      </template>
    </div>

    <!-- Empty state -->
    <div
      v-if="!flowStore.loading && flowStore.items.length === 0"
      class="text-center py-12 text-surface-400"
    >
      {{ t('flow.noTransactions') }}
    </div>

    <!-- Loading / sentinel -->
    <div ref="sentinelRef" class="py-4 text-center">
      <span v-if="flowStore.loading" class="text-sm text-surface-400">
        <i class="pi pi-spinner pi-spin mr-2"></i>{{ t('flow.loadingMore') }}
      </span>
    </div>
  </div>
</template>
