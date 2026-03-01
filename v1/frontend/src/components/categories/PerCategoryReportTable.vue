<template>
  <div>
    <section class="columns">
      <b-field class="column" grouped >
        <b-field class="buttons" grouped>
          <b-field><b-button size="is-small" :disabled="allCategoriesExpanded" @click="expandAllCategories">{{ $t('stats.table.expand_all') }}</b-button></b-field>
          <b-field><b-button size="is-small" :disabled="allCategoriesCollapsed" @click="collapseAllCategories">{{ $t('stats.table.collapse_all') }}</b-button></b-field>
        </b-field>
        <b-field>
          <b-switch v-model="showZeroRows" type="is-success" passive-type='is-danger'>{{ $t('stats.table.show_zeroes') }}</b-switch>
        </b-field>
      </b-field>
    </section>
    <section class="table-container">
      <table class="table">
        <thead>
          <tr class="period-row">
            <th colspan="2"><!-- Empty first header--></th>
            <th v-for="period in periods" :key="period.name">{{ period.name }}</th>
          </tr>
          <tr class="unlabeled-row">
            <th colspan="2">{{ $t('stats.table.total') }}</th>
            <th class="amountCell" v-for="period in periods" :key="period.name">
              <currency-display :currency="defaultCurrency" :amount="getPeriodTotal(period)" do-color/>
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Unlabeled-->
          <tr class="top-level-row">
            <th colspan="2"><div class="category-header"><p class="category-name">{{ $t('stats.category.unlabeled') }}</p></div></th>
            <td class="amountCell"  v-for="period in periods" :key="period.name" :set="bucket = getAugmentedBucketByCategory(period, null)">
              <div v-if="bucket.totalAmount !== null">
                <currency-display :currency="bucket.currency" :amount="bucket.totalAmount" do-color></currency-display>
              </div>
              <div v-else><string-or-null-display :value="null"/> </div>
            </td>
          </tr>
        </tbody>
        <tbody v-for="(category, idx) in visibleCategories" :key="category.id">
          <tr :class="category.id_parent ? (idx % 2 ? 'alternate-row' : '') : 'top-level-row'">
            <th class="toggle-expand-button">
              <b-button 
                v-if="!category.id_parent"
                size="is-small"
                type="is-ghost"
                :icon-left="categoryExpanded[category.id] ? 'chevron-up' : 'chevron-down'" 
                @click="toggleCategoryExpanded(category)"
              />
            </th>
            <th><div class="category-header"><category-tag :category="category" use-tag-color/><p class="category-name">{{ category.name }}</p></div></th>
            <td class="amountCell" v-for="period in periods" :key="period.name" :set="bucket = getAugmentedBucketByCategory(period, category)">
              <currency-display :currency="bucket.currency" :amount="bucket.totalAmount" do-color reduce-alpha-on-zero />
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import { strcurrency } from '@/utils/helpers';
import CategoryTag from '@/components/categories/CategoryTag.vue';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import Currency from '@/utils/api/Currency';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay'

export default defineComponent({
  components: { CategoryTag, CurrencyDisplay, StringOrNullDisplay },
  props: {
    // raw category tree
    categories: { type: Array, required: true },
    // array of {name: "period name", buckets: Array }
    // the stats array is simply the raw list of category buckets for the period 
    periods: { type: Array, required: true },
    defaultCurrency: { type: Currency, required: true },
    expandTopLevel: { type: Boolean, default: true }
  },
  data() {
    return {
      categoryExpanded: {},
      showZeroRows: false
    };
  },
  created() {
    this.resetExpandedCategories();
  },
  computed: {
    visibleCategories() {
      return this.categories.flatMap(c => this.flattenCategory(c)).filter(c => this.isCategoryVisible(c));
    },
    categoriesWithData() {
      let categoriesWithData = new Set();
      for (let period of this.periods) {
        for (let bucket of period.buckets) {
          categoriesWithData.add(bucket.id_category);
        }
      }
      return categoriesWithData;
    },
    allCategoriesExpanded() {
      return Object.values(this.categoryExpanded).every(v => v);
    },
    allCategoriesCollapsed() {
      return Object.values(this.categoryExpanded).every(v => !v);
    }
  },
  methods: {
    getAugmentedBucketByCategory(period, category) {
      // this function traverses the category tree, it is O(T) where T is the number of categories
      // buckets are augmented with a field totalAmount which also accounts for subcategories incomes/expenses
      let categoryId = category ? category.id : null;
      let bucket = period.buckets.find(b => b.id_category === categoryId);
      
      // unlabeled bucket
      if (!category) { 
        if (!bucket) { // no unlabeled bucket
          return this.makeEmptyAugmentedBucket(null, null, null, this.defaultCurrency); // differentiate 0 and no value for proper display in the table
        } else {
          bucket.totalAmount = bucket.amount;
          return bucket;
        }
      }

      // if not child category, amount is already right
      if (category.children.length === 0) {
        if (!bucket) {
          return this.makeEmptyAugmentedBucket(0, category, category.id, this.defaultCurrency); 
        } else {
          bucket.totalAmount = bucket.amount;
          return bucket;
        } 
      }

      // need to account for income/expense of descendants
      let descendants = this.getDescendantCategories(category);
      let descendantIds = new Set(descendants.map(c => c.id));
      let descendantBuckets = period.buckets.filter(b => descendantIds.has(b.id_category));

      if (descendantBuckets.length === 0) {
        return this.makeEmptyAugmentedBucket(0, category, category.id, this.defaultCurrency);
      }

      if (!bucket) {
        // no direct bucket so create a new one to avoid
        // overwriting other real buckets (keep the corresponding currency)
        bucket = this.makeEmptyAugmentedBucket(0, category, category.id, descendantBuckets[0].currency);
      } else {
        bucket.totalAmount = strcurrency(bucket.amount).value;
      }

      for (let i = 0; i < descendantBuckets.length; i++) {
        let descendantBucket = descendantBuckets[i];
        bucket.totalAmount += strcurrency(descendantBucket.amount).value;
      }

      return bucket;
    },
    makeEmptyAugmentedBucket(totalAmount, category, categoryId, currency) {
      return {
        currency: currency,
        id_currency: currency.id,
        category: category,
        id_category: categoryId,
        amount: 0,
        totalAmount: totalAmount // differentiate 0 and no value for proper display in the table
      };
    },
    getDescendantCategories(category) {
      /** Get children categories of the current category */
      if (!category.children) {
        return [];
      }
      let children = [...category.children];
      for (let child of children) {
        children.push(...this.getDescendantCategories(child));
      }
      return children;
    },
    flattenCategory(category) {
      if (category.children) {
        return [category, ...category.children.flatMap(c => this.flattenCategory(c))];
      } else {
        return [category];
      }
    },
    getPeriodTotal(period) {
      // TODO optimize
      return period.buckets.reduce((total, stat) => {
        let parsed = strcurrency(stat.amount);
        return total + parsed.value;
      }, 0)
    },
    setExpandedCategories(resetState) {
      let expanded = {};
      for (let category of this.categories) {
        expanded[category.id] = resetState;
      }
      this.categoryExpanded = expanded;
    },
    resetExpandedCategories() {
      this.setExpandedCategories(this.expandTopLevel);
    },
    isCategoryVisible(category) {
      return !category.id_parent || (this.categoryExpanded[category.id_parent] && (this.showZeroRows || this.categoriesWithData.has(category.id)));
    },
    toggleCategoryExpanded(category) {
      this.categoryExpanded[category.id] = !this.categoryExpanded[category.id];
    },
    expandAllCategories() {
      this.setExpandedCategories(true);
    },
    collapseAllCategories() {
      this.setExpandedCategories(false);
    }
  }
});
</script>

<style scoped>
/* general table general formatting */
table tbody, table thead .unlabeled-row {
  font-size: 75%;
}

table thead .period-row {
  text-align: center;
}

td, th {
  vertical-align: middle;
  padding-top: 2px;
  padding-bottom: 2px;
}
.top-level-row {
  background-color: rgb(222, 222, 222); /* Grey background */
  
  border-top: 1px solid rgb(191, 191, 191);
  border-collapse: collapse;
}

.alternate-row {
  background-color: rgb(242, 242, 242); /* Lighter grey background */
}

/* Category name cell*/
.category-header {
  display: flex;
  align-items: center;
}

.category-name {
  margin-left: 5px;
  vertical-align: middle;
}

.amountCell, th.amountCell {
  text-align: right;
}

/* In table components */
.toggle-expand-button {
  padding-left: 0;
  padding-right: 0;
}
</style>