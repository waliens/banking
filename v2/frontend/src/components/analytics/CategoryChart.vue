<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Chart from 'primevue/chart'

const props = defineProps({
  data: { type: Object, default: null },
})

const { t } = useI18n()

const defaultColors = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

const chartData = computed(() => {
  if (!props.data?.items?.length) return null

  const items = props.data.items
  return {
    labels: items.map((i) => i.category_name || t('transactions.uncategorized')),
    datasets: [
      {
        data: items.map((i) => Number(i.amount)),
        backgroundColor: items.map((i, idx) => i.category_color || defaultColors[idx % defaultColors.length]),
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' },
  },
}
</script>

<template>
  <div v-if="chartData" class="h-80">
    <Chart type="doughnut" :data="chartData" :options="chartOptions" />
  </div>
  <p v-else class="text-surface-500 text-center py-8">{{ t('wallet.noData') }}</p>
</template>
