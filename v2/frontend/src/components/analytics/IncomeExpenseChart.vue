<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Chart from 'primevue/chart'

const props = defineProps({
  data: { type: Object, default: null },
})

const { t } = useI18n()

const chartData = computed(() => {
  if (!props.data?.items?.length) return null

  const items = props.data.items
  const labels = items.map((i) => `${i.year}-${String(i.month).padStart(2, '0')}`)

  return {
    labels,
    datasets: [
      {
        label: t('wallet.income'),
        backgroundColor: '#22c55e',
        data: items.map((i) => Number(i.income)),
      },
      {
        label: t('wallet.expense'),
        backgroundColor: '#ef4444',
        data: items.map((i) => Number(i.expense)),
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top' },
  },
  scales: {
    y: { beginAtZero: true },
  },
}
</script>

<template>
  <div v-if="chartData" class="h-80">
    <Chart type="bar" :data="chartData" :options="chartOptions" />
  </div>
  <p v-else class="text-surface-500 text-center py-8">{{ t('wallet.noData') }}</p>
</template>
