<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import SelectButton from 'primevue/selectbutton'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'

const props = defineProps({
  periodType: { type: String, default: 'year' },
  year: { type: Number, default: () => new Date().getFullYear() },
  month: { type: Number, default: () => new Date().getMonth() + 1 },
  dateFrom: { type: [Date, String], default: null },
  dateTo: { type: [Date, String], default: null },
  showMonthOption: { type: Boolean, default: true },
})

const emit = defineEmits(['update:periodType', 'update:year', 'update:month', 'update:dateFrom', 'update:dateTo', 'change'])

const { t } = useI18n()

const periodTypeOptions = computed(() => {
  const opts = [
    { label: t('wallet.periodYear'), value: 'year' },
  ]
  if (props.showMonthOption) {
    opts.push({ label: t('wallet.periodMonth'), value: 'month' })
  }
  opts.push({ label: t('wallet.periodRange'), value: 'range' })
  return opts
})

const currentYear = new Date().getFullYear()
const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 10; y--) {
    years.push({ label: String(y), value: y })
  }
  return years
})

const monthOptions = computed(() => {
  const months = []
  for (let m = 1; m <= 12; m++) {
    const d = new Date(2000, m - 1)
    months.push({ label: d.toLocaleString('default', { month: 'long' }), value: m })
  }
  return months
})

function onPeriodTypeChange(val) {
  emit('update:periodType', val)
  emit('change')
}

function onYearChange(val) {
  emit('update:year', val)
  emit('change')
}

function onMonthChange(val) {
  emit('update:month', val)
  emit('change')
}

function onDateFromChange(val) {
  emit('update:dateFrom', val)
  emit('change')
}

function onDateToChange(val) {
  emit('update:dateTo', val)
  emit('change')
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-3">
    <SelectButton
      :modelValue="periodType"
      @update:modelValue="onPeriodTypeChange"
      :options="periodTypeOptions"
      optionLabel="label"
      optionValue="value"
      :allowEmpty="false"
    />

    <!-- Year selector (shown for year and month types) -->
    <Select
      v-if="periodType === 'year' || periodType === 'month'"
      :modelValue="year"
      @update:modelValue="onYearChange"
      :options="yearOptions"
      optionLabel="label"
      optionValue="value"
      class="w-28"
    />

    <!-- Month selector (shown for month type only) -->
    <Select
      v-if="periodType === 'month'"
      :modelValue="month"
      @update:modelValue="onMonthChange"
      :options="monthOptions"
      optionLabel="label"
      optionValue="value"
      class="w-36"
    />

    <!-- Date range pickers -->
    <template v-if="periodType === 'range'">
      <DatePicker
        :modelValue="dateFrom"
        @update:modelValue="onDateFromChange"
        dateFormat="yy-mm-dd"
        :placeholder="t('transactions.date')"
        showIcon
        class="w-40"
      />
      <span class="text-surface-500">—</span>
      <DatePicker
        :modelValue="dateTo"
        @update:modelValue="onDateToChange"
        dateFormat="yy-mm-dd"
        :placeholder="t('transactions.date')"
        showIcon
        class="w-40"
      />
    </template>
  </div>
</template>
