<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import CurrencyDisplay from '../common/CurrencyDisplay.vue'

const { t } = useI18n()

const props = defineProps({
  group: { type: Object, required: true },
  direction: { type: String, required: true },
  mobile: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

const displayAmount = computed(() => {
  if (!props.group.transactions) return 0
  const amount = props.group.transactions.reduce((sum, tx) => sum + Number(tx.effective_amount ?? tx.amount), 0)
  return props.direction === 'expense' ? -amount : amount
})

</script>

<template>
  <!-- Mobile card -->
  <div
    v-if="mobile"
    class="bg-surface-0 rounded-lg shadow-sm p-3 cursor-pointer hover:shadow-md transition-shadow"
    :class="direction === 'income' ? 'border-l-4 border-green-400' : 'border-l-4 border-red-400'"
    @click="emit('select', group.transactions?.[0]?.id)"
  >
    <div class="flex items-center justify-between gap-2">
      <span class="text-sm truncate flex-1 font-medium">{{ group.name || `Group #${group.id}` }}</span>
      <span class="text-sm font-semibold whitespace-nowrap">
        <CurrencyDisplay :amount="displayAmount" colored />
      </span>
    </div>
    <div class="text-xs text-surface-400 mt-1">
      {{ t('flow.transactionsCount', { count: group.transactions?.length || 0 }) }}
    </div>
  </div>

  <!-- Desktop card -->
  <div
    v-else
    class="relative rounded-lg shadow-sm p-3 cursor-pointer hover:shadow-md transition-shadow border border-dashed"
    :class="[
      direction === 'income' ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300',
      direction === 'income' ? 'mr-3' : 'ml-3',
    ]"
    @click="emit('select', group.transactions?.[0]?.id)"
  >
    <!-- Arrow notch -->
    <div
      class="absolute top-1/2 -translate-y-1/2 w-0 h-0"
      :class="
        direction === 'income'
          ? 'right-[-8px] border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent border-l-[8px] border-l-green-50'
          : 'left-[-8px] border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent border-r-[8px] border-r-red-50'
      "
    ></div>
    <div class="flex items-center justify-between gap-2">
      <span class="text-sm truncate flex-1 font-medium">{{ group.name || `Group #${group.id}` }}</span>
      <span class="text-sm font-semibold whitespace-nowrap">
        <CurrencyDisplay :amount="displayAmount" colored />
      </span>
    </div>
    <div class="text-xs text-surface-400 mt-1">
      {{ t('flow.transactionsCount', { count: group.transactions?.length || 0 }) }}
    </div>
  </div>
</template>
