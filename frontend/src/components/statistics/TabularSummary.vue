<template>
  <div v-if="visible">
    <section class="level">
      <div class="level-item level-center" >
      
      </div>
    </section>
    <section v-if="true">
      <per-category-report-table :categories="categoryTree" :periods="periods" :default-currency="defaultCurency"></per-category-report-table>
    </section>
    <section v-else>
      <no-data-box height="400px" width="80%"></no-data-box>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import NoDataBox from '../generic/NoDataBox.vue';
import Currency from '@/utils/api/Currency';
import Category from '@/utils/api/Category';
import PerCategoryReportTable from '@/components/categories/PerCategoryReportTable';

export default defineComponent({
  props: {
    'group': Object,
    'visible': {type: Boolean, default: true}
  },
  components: {NoDataBox, PerCategoryReportTable},
  data() {
    return {
      categoryTree: [],
      periods: []
    };
  },
  computed: {
    defaultCurency() {
      let currencies = this.group.account_groups.map(ag => ag.account.currency);
      return new Currency(currencies[0]);
    },
    lastTenYears() {
      let years = [];
      for (let i = 0; i < 10; i++) {
        years.push(new Date().getFullYear() - i);
      }
      return years;
    }
  },
  async created() {
    // fetch and sort
    let tree = await Category.getCategoryTree();
    this.sortCategoryTreeByNames(tree);
    this.categoryTree = tree; 
    // fetch stats
    this.fetchPeriods();
  },
  methods: {
    // Sorting table
    sortCategoryTree(tree, compareCategories) {
      // iterate over tree nodes' children
      for (let i = 0; i < tree.length; i++){
        if (tree[i].children && tree[i].children.length > 0) {
          this.sortCategoryTree(tree[i].children, compareCategories);
        }
      } 
      tree.sort(compareCategories);
    },
    sortCategoryTreeByNames(tree) {
      this.sortCategoryTree(tree, (a, b) => a.name.localeCompare(b.name));
    },
    async fetchPeriods() {
      let years = this.lastTenYears;
      this.periods = await Promise.all(
        years.map(year => this.group.getPerCategoryStats({
          period_from: `${year}-01-01`,
          period_to: `${year}-12-31`,
          level: -1
        }))
      ).then(allPeriodBuckets => {
        return allPeriodBuckets.map((periodBuckets, i) => ({name: `Y${years[i]}`, value: years[i], buckets: periodBuckets}));
      });
    },
  }
});
</script>
