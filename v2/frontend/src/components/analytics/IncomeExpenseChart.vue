<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWalletStore } from '../../stores/wallets'
import Chart from 'primevue/chart'
import Select from 'primevue/select'

const props = defineProps({
  walletId: { type: Number, required: true },
})

const { t } = useI18n()
const walletStore = useWalletStore()

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)
const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 10; y--) {
    years.push({ label: String(y), value: y })
  }
  return years
})

const isMobile = ref(false)
const data = ref(null)

function checkMobile() {
  isMobile.value = window.innerWidth < 640
}

async function loadData() {
  if (!props.walletId) return
  data.value = await walletStore.fetchIncomeExpense(props.walletId, { year: selectedYear.value })
}

const chartData = computed(() => {
  if (!data.value?.items?.length) return null

  const items = data.value.items
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

const chartOptions = computed(() => {
  const base = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
  }

  if (isMobile.value) {
    return {
      ...base,
      indexAxis: 'y',
      scales: {
        x: { beginAtZero: true },
      },
    }
  }

  return {
    ...base,
    scales: {
      y: { beginAtZero: true },
    },
  }
})

const chartHeight = computed(() => {
  if (isMobile.value && data.value?.items?.length) {
    return Math.max(300, data.value.items.length * 50)
  }
  return 320
})

watch(() => props.walletId, loadData)
watch(selectedYear, loadData)

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4 mt-2">
      <label class="text-sm font-medium">{{ t('wallet.year') }}</label>
      <Select
        v-model="selectedYear"
        :options="yearOptions"
        optionLabel="label"
        optionValue="value"
        class="w-32"
      />
    </div>

    <div v-if="chartData" :style="{ height: chartHeight + 'px' }">
      <Chart type="bar" :data="chartData" :options="chartOptions" />
    </div>
    <p v-else class="text-surface-500 text-center py-8">{{ t('wallet.noData') }}</p>
  </div>
</template>
