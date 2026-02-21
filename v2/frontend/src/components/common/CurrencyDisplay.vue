<script setup>
import { computed } from 'vue'

const props = defineProps({
  amount: { type: [Number, String], required: true },
  currencySymbol: { type: String, default: '' },
  colored: { type: Boolean, default: false },
  showSign: { type: Boolean, default: false },
  decimals: { type: Number, default: 2 },
})

const numericAmount = computed(() => Number(props.amount))

const formattedAmount = computed(() => {
  const abs = Math.abs(numericAmount.value)
  const formatted = abs.toLocaleString('en', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  })
  const sign = props.showSign
    ? numericAmount.value > 0 ? '+' : numericAmount.value < 0 ? '-' : ''
    : numericAmount.value < 0 ? '-' : ''
  return `${sign}${formatted}`
})

const colorClass = computed(() => {
  if (!props.colored) return ''
  if (numericAmount.value > 0) return 'text-green-600'
  if (numericAmount.value < 0) return 'text-red-500'
  return 'text-surface-400'
})
</script>

<template>
  <span :class="colorClass">{{ formattedAmount }} {{ currencySymbol }}</span>
</template>
