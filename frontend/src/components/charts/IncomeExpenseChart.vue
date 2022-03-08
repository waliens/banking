<template>
  <div>
    <section class="level">
      <div class="level-item level-center" >
        <b-field :label="$t('year')" label-position="on-border">
          <b-select v-model="selectedYear" @input="onYearChange">
            <option v-for="year in getYears()" :key="year" :value="year">
              {{year}}
            </option>
          </b-select>
        </b-field>
      </div>
    </section>
    <section v-if="chartData.length > 1">
      <GChart :data="chartData" :options="options" type="ColumnChart"></GChart>
    </section>
    <section v-else>
      <no-data-box height="400px" width="80%"></no-data-box>
    </section>
  </div>  
</template>

<script>
import moment from 'moment';
import { strcurrency, monthMap } from '@/utils/helpers';
import { defineComponent } from '@vue/composition-api';
import { GChart } from 'vue-google-charts';
import NoDataBox from '../generic/NoDataBox.vue';

export default defineComponent({
  components: {GChart, NoDataBox},
  props: {'group': Object},
  data() {
    return {
      selectedYear: this.getCurrentYear(),
      chartData: [],
      options: {
        title: this.$t('charts.incomeexpense.title'),
        chartArea: {width: '80%'},
        hAxis: {
          minValue: Math.max(...this.getYears()),
        },
        vAxis: {
          title: 'currency'
        },
        colors: ['#63be7b', '#f8696b']
      }
    }
  },
  async created() {
    this.chartData = await this.generateChartData();
  },
  computed: {
    monthMap() {
      return monthMap(this);
    }
  },
  methods: {
    getYears() {
      let length = 20; 
      return Array.from({length}, (_, i) => this.getCurrentYear() + i - length + 1);
    },
    getCurrentYear() {
      return moment().year();
    },
    async getRawStats() {
      return await this.group.getIncomesExpensesStats(this.selectedYear);
    },
    async generateChartData() {
      let rawStats = await this.getRawStats();
      let map = {}, foundMonths = [];
      if (rawStats.currencies.length != 1) {
        // several currencies in list
        return [];
      } else {
        this.options.vAxis.title = `${rawStats.currencies[0].long_name} (${rawStats.currencies[0].symbol})`;
      }
      rawStats.incomes.forEach(entry => {
        foundMonths.push(entry.month);
        map[entry.month] = {};
        map[entry.month].income = strcurrency(entry.total).value;
      });
      rawStats.expenses.forEach(entry => {
        if (!map[entry.month]) {
          map[entry.month] = {};
        }
        map[entry.month].expense = strcurrency(entry.total).value
      });
      foundMonths.sort((a, b) => a - b);

      // generate actual chart data
      let data = new Array();
      data.push(new Array(this.$t('month'), this.$t('charts.incomeexpense.incomes'), this.$t('charts.incomeexpense.expenses')));
      foundMonths.forEach(month => {
        let month_data = map[month];
        if (!month_data) {
          month_data = {};
        }
        data.push(new Array(`${this.monthMap[month]}`, ...[map[month].income || 0, map[month].expense || 0]));
      })
      return data;
    },
    async onYearChange(newValue) {
      this.selectedYear = newValue;
      this.chartData = await this.generateChartData();
    }
  }
})
</script>
