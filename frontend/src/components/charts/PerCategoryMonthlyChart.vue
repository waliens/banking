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
        <b-field :label="$t('year')" label-position="on-border">
          <b-select v-model="selectedYear" @input="updateGraph">
            <option v-for="year in getYears()" :key="year" :value="year">
              {{year}}
            </option>
          </b-select>
        </b-field>
      </div>
      <div class="column">
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
        </b-field>
      </div>
      <div class="column">
        <b-field>
          <b-switch v-model="includeUnlabeled" @input="updateGraph">{{$t('stats.category.unlabeled')}}</b-switch>
        </b-field>
      </div>
    </section>
    <section v-if="chartData.length > 1">
      <GChart :data="chartData" :options="chartOptions" :events="chartEvents" type="ColumnChart"></GChart>
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
      includeUnlabeled: false,
      detailLevel: 0,
      minDetailLevel: 0,
      maxDetailLevel: 0,
      detailLevelOptions: [],
      coarseCategoryId: null,
      categories: {},
      selectedYear: null,
      chartData: [],
      chartOptions: {},
      chartColItemToCategory: [],
      chartEvents: {
        click: this.chartClicked
      }
    }
  },
  async created() {
    this.selectedYear = this.getCurrentYear();
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
    getStatsQueryParams() {
      return {
        ... this.getPeriodRange(),
        income_only: this.showIncomes,
        level: this.detailLevel,
        id_category: this.coarseCategoryId,
        unlabeled: this.includeUnlabeled
      }
    },
    getPeriodRange() {
      let formatStr = "YYYY-MM-DD";
      let year = moment({"year": this.selectedYear});
      return {
        period_from: year.startOf("year").format(formatStr), 
        period_to: year.endOf("year").format(formatStr)
      };
    },
    monthMap() {
      return monthMap(this);
    },
    async updateLevelSelector() {
      this.coarseCategoryId = null;
      await this.updateGraph();
    },
    async getRawStats() {
      return await this.group.getPerCategoryMonthlyStats(this.getStatsQueryParams());
    },
    async generateChartDataAndOptions() {
      let monthBuckets = await this.getRawStats();
      // list all categories appearing in stats
      let foundCategories = {};
      let foundMonths = [];
      Object.entries(monthBuckets).forEach(vs => {
        let month = vs[0], monthBucket = vs[1];
        foundMonths.push(parseInt(month));
        monthBucket.forEach(bucket => {
          foundCategories[bucket.id_category || -1] = {
            name: bucket.id_category ? bucket.category.name : this.$t('stats.category.unlabeled'),
            color: bucket.id_category ? bucket.category.color : "#555555",
            id: bucket.id_category ? bucket.id_category : -1,
            category: bucket.id_category ? bucket.category : null
          }
        });
      });
      let sortedCategories = Object.entries(foundCategories).map(vs => vs[0]);
      sortedCategories.sort((a, b) => b - a);  // to have unlabeled at the end 

      let data = foundMonths.map(monthNumber => {
          let monthStr = monthNumber.toString();
          let buckets = monthBuckets[monthStr];
          buckets.sort((a, b) => (b.id_category || -1) - (a.id_category || -1));
          let dataRow = [this.monthMap()[monthNumber - 1]]
          for (let categIndex = 0, bucketIndex = 0; categIndex < sortedCategories.length; categIndex++) {
            let categIdentifier = sortedCategories[categIndex];
            let category = foundCategories[categIdentifier];
            let bucket = buckets[bucketIndex];
            if (bucket && category.id == (bucket.id_category || -1)) {
              dataRow.push(strcurrency(bucket.amount).value);
              bucketIndex++;
            } else {
              dataRow.push(0);
            }
          }
          return dataRow;
      });
      data.unshift(['Category', ...sortedCategories.map(categId => foundCategories[categId].name)]);
      let options = {
        title: this.coarseCategoryId ? this.coarseCategory.nestedName : "",
        chartArea: {width: '80%', height: 400},
        height: 500,
        colors: sortedCategories.map(categId => foundCategories[categId].color),
        bar: { groupWidth: '75%' },
        isStacked: true,
      };
      return {options, data, colItemToCategory: sortedCategories.map(id => foundCategories[id].category)};
    },
    async updateGraph() {
      let {data, options, colItemToCategory} = await this.generateChartDataAndOptions();
      this.chartData = data;
      this.chartOptions = options; 
      this.chartColItemToCategory = colItemToCategory;
    },
    async chartClicked(e) {
      let colItemId = parseInt(e.targetID.split("#")[1]);
      let bucket = this.chartColItemToCategory[colItemId];
      if (this.detailLevel < this.maxDetailLevel && bucket) {
        this.detailLevel = parseInt(this.detailLevel) + 1;
        this.coarseCategoryId = bucket.id;
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
