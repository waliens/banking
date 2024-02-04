<template>
  <div v-if="visible">
    <section class="columns">
      <div class="column">
        <b-field>
          <b-switch
            v-model="showIncomes"
            type="is-success"
            passive-type='is-danger'
            @input="switchedShowIncomes"
            >
            <span v-if="showIncomes">{{ $t('stats.switch.incomes') }}</span>
            <span v-else>{{ $t('stats.switch.expenses') }}</span>
          </b-switch>
        </b-field>
      </div>
      <div class="column">
        <b-field grouped>
          <b-field :label="$t('stats.category.period_selector')" label-position="on-border">
            <b-select v-model="periodType" @input="updateGraph">
              <option v-for="_type in periodTypeOptions" :key="_type.id" :value="_type.id">
                {{_type.name}}
              </option>
            </b-select>
          </b-field>
          <b-field v-if="periodType == 'month'" :label="$t('month')" label-position="on-border">
            <b-select v-model="selectedMonth" @input="updateGraph">
              <option v-for="month in getMonths()" :key="month.number" :value="month.number">
                {{month.name}}
              </option>
            </b-select>
          </b-field>
          <b-field v-if="periodType != 'between'" :label="$t('year')" label-position="on-border">
            <b-select v-model="selectedYear" @input="updateGraph">
              <option v-for="year in getYears()" :key="year" :value="year">
                {{year}}
              </option>
            </b-select>
          </b-field>
          <b-field v-if="periodType == 'between'" :label="$t('stats.category.period_trom')" label-position="on-border" expanded>
            <b-datepicker
              v-model="periodFromDate"
              :show-week-number="true"
              icon="calendar-today"
              icon-right-clickable
              @icon-right-click="clearPeriodFrom"
              trap-focus
              @input="updateGraph">
            </b-datepicker>
          </b-field>
          <b-field v-if="periodType == 'between'" :label="$t('stats.category.period_to')" label-position="on-border" expanded>
            <b-datepicker
              v-model="periodToDate"
              :show-week-number="true"
              icon="calendar-today"
              icon-right-clickable
              @icon-right-click="clearPeriodTo"
              trap-focus
              @input="updateGraph">
            </b-datepicker>
          </b-field>
        </b-field>
      </div>
      <div class="column" is-vcentered >
        <b-field grouped>
          <b-field>
            <b-tooltip :label="$t('up')">
              <b-button icon-right="angle-up" :disabled="detailLevel <= minDetailLevel" @click="goUpOneLevel"></b-button>
            </b-tooltip>
          </b-field>
          <b-field  :label="$t('stats.category.level_selector')" label-position="on-border">
            <b-select v-model="detailLevel" @input="updateLevelSelector">
              <option v-for="level in detailLevelOptions" :key="level.value" :value="level.value">
                {{level.name}}
              </option>
            </b-select>
          </b-field>
          <b-field v-if="coarseCategories && coarseCategories.length > 0" :label="$t('stats.category.coarse_category')" label-position="on-border">
            <b-select v-model="coarseCategoryId" @input="updateGraph">
              <option v-for="category in coarseCategories" :key="category.id" :value="category.id">
                {{category.nestedName}}
              </option>
            </b-select>
          </b-field>
          <b-field>
            <b-switch v-model="includeUnlabeled" @input="updateGraph">{{$t('stats.category.unlabeled')}}</b-switch>
          </b-field>
        </b-field>
      </div>
    </section>
    <section v-if="chartData.length > 1">
      <GChart :data="chartData" :options="chartOptions" :events="chartEvents" type="PieChart"></GChart>
    </section>
    <section v-else>
      <no-data-box height="400px" width="80%"></no-data-box>
    </section>
  </div>  
</template>

<script>
import moment from 'moment';
import { monthMap, strcurrency } from '@/utils/helpers';
import { defineComponent } from '@vue/composition-api';
import { GChart } from 'vue-google-charts';
import NoDataBox from '../generic/NoDataBox.vue';
import Category from '@/utils/api/Category';

export default defineComponent({
  components: {GChart, NoDataBox},
  // visible: to allow rendering only when the graph is visible to avoid relative with issue when component is not on the page
  props: {'group': Object, 'visible': {type: Boolean, default: true} },
  name: "PerCategoryChart",
  data() {
    return {
      // income expense switch
      showIncomes: true,
      // period filters
      periodType: 'between',
      periodTypeOptions: [
        {id: 'month', name: this.$t('stats.category.period_type_month') },
        {id: 'year', name: this.$t('stats.category.period_type_year') },
        {id: 'between', name: this.$t('stats.category.period_type_between') }
      ],
      selectedYear: null,
      selectedMonth: null,
      periodFrom: null,
      periodTo: null,
      // label exploration
      includeUnlabeled: false,
      detailLevel: 0,
      minDetailLevel: 0,
      maxDetailLevel: 0,
      detailLevelOptions: [],
      coarseCategoryId: null,
      categories: {},
      // chart data
      chartData: [],
      chartOptions: {},
      chartSliceToCategory: {},
      chartEvents: {
        click: this.pieChartClicked
      }
    }
  },
  async created() {
    this.selectedYear = this.getCurrentYear();
    this.selectedMonth = this.getCurrentMonth();
    this.periodFrom = moment().subtract(10, "years");
    this.periodTo = moment().add(1, "day");
    this.categories = await Category.getCategoryTreeByDepth();

    // build detail level options
    let levels = Object.keys(this.categories).filter(level => this.categories[level].length > 0);
    this.minDetailLevel = Math.min(...levels);
    this.maxDetailLevel = Math.max(...levels); 
    this.detailLevelOptions = levels.map(level => {
      let name = `${level}`;
      if (level == this.minDetailLevel) {
        name = `${name} (${this.$t('stats.category.level_coarsest')})`
      } else if (level == this.maxDetailLevel) {
        name = `${name} (${this.$t('stats.category.level_finest')})`
      }
      return { value: level, name }
    });

    await this.updateGraph();
  },
  computed: {
    coarseCategory() {
      if (!this.coarseCategoryId || !this.categories) {
        return null;
      }
      let results = this.categories[this.detailLevel - 1].filter(c => c.id == this.coarseCategoryId);
      if (results.length == 0) {
        return null;
      }
      return results[0];
    },
    coarseCategories() {
      if (!this.detailLevel || !this.categories || this.detailLevel == this.minDetailLevel) {
        return [];
      }
      return this.categories[this.detailLevel - 1];
    },
    monthMap() {
      return monthMap(this);
    },
    periodFromDate: {
      get() {
        return this.periodFrom ? this.periodFrom.toDate() : null;
      },
      set(value) {
        this.periodFrom = value ? moment(value) : null;
      }
    },
    periodToDate: {
      get() {
        return this.periodTo ? this.periodTo.toDate() : null;
      },
      set(value) {
        this.periodTo = value ? moment(value) : null;
      }
    }
  },
  methods: {
    getEmptyChartDataObject() {
      return {
        data: [],
        options: {},
        sliceToCategory: {}
      };
    },
    getYears() {
      let length = 20; 
      return Array.from({length}, (_, i) => this.getCurrentYear() + i - length + 1);
    },
    getCurrentYear() {
      return moment().year();
    },
    getMonths() {
      let length = 12;
      return Array.from({length}, (_, i) => { return {name: this.monthMap[i], number: i}; });
    },
    getCurrentMonth() {
      return moment().month();
    },
    clearPeriodFrom() { 
      this.periodFrom = null;  
    },
    clearPeriodTo() { 
      this.periodTo = null; 
    },
    async getRawStats() {
      return await this.group.getPerCategoryStats(this.getStatsQueryParams());
    },
    getStatsQueryParams() {
      return {
        ... this.getPeriodRange(),
        level: this.detailLevel,
        id_category: this.coarseCategoryId,
        unlabeled: this.includeUnlabeled,
        income_only: this.showIncomes
      }
    },
    getPeriodRange() {
      let formatStr = "YYYY-MM-DD";
      if (this.periodType == 'year') {
        let year = moment({"year": this.selectedYear});
        return {
          period_from: year.startOf("year").format(formatStr), 
          period_to: year.endOf("year").format(formatStr)
        }
      } else if (this.periodType == 'month') {
        let month = moment({"month": this.selectedMonth, "year": this.selectedYear});
        return {
          period_from: month.startOf('month').format(formatStr), 
          period_to: month.endOf('month').format(formatStr)
        }
      } else {
        return {
          period_from: this.periodFrom.format(formatStr), 
          period_to: this.periodTo.format(formatStr)
        }
      }
    },
    async updateLevelSelector() {
      this.coarseCategoryId = null;
      await this.updateGraph();
    },
    async generateChartDataAndOptions() {
      let buckets = await this.getRawStats();
      if (Object.keys(buckets).length == 0) {
        return this.getEmptyChartDataObject();
      }
      let data = buckets.map(bucket => {
        let name = bucket.id_category ? bucket.category.name : this.$t('stats.category.unlabeled');
        let value = strcurrency(bucket.amount).value;
        return [name, value];
      });
      let options = {
        'slices': {},
        title: this.coarseCategoryId ? this.coarseCategory.nestedName : "",
        chartArea: {width: '80%', height: 400},
        height: 500,
        sliceVisibilityThreshold: 0.02
      };
      let sliceToCategory = {};
      let counter = 0;
      buckets.forEach(bucket => {
        if (bucket.id_category) {
          options.slices[counter] = {color: bucket.category.color};
        } else {
          options.slices[counter] = {color: "#555555"};
        }
        sliceToCategory[counter] = bucket;
        counter++;
      });
      return {options, data: [[this.$t('stats.category.category'), this.$t('amount')], ...data], sliceToCategory};
    },
    async updateGraph() {
      let {data, options, sliceToCategory} = await this.generateChartDataAndOptions();
      this.chartData = data;
      this.chartOptions = options; 
      this.chartSliceToCategory = sliceToCategory;
    },
    async pieChartClicked(e) {
      let sliceId = parseInt(e.targetID.split("#")[1]);
      let bucket = this.chartSliceToCategory[sliceId];
      if (this.detailLevel < this.maxDetailLevel && bucket.id_category) {
        this.detailLevel = parseInt(this.detailLevel) + 1;
        this.coarseCategoryId = bucket.category.id;
        await this.updateGraph();
      }
    },
    async goUpOneLevel() {
      if (this.coarseCategory) {
        this.coarseCategoryId = this.coarseCategory.id_parent || null;
      }
      this.detailLevel = parseInt(this.detailLevel) - 1;
      await this.updateGraph();
    },
    async switchedShowIncomes() {
      await this.updateGraph();
    }
  }
})
</script>
