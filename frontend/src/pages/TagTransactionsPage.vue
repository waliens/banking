<template>
  <div>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('tagging.title')}}</h3></div>
    </section>
    <section>
      <b-table
        :data="transactions"
        paginated
        :backend-pagination="true"
        @page-change="onPageChange"
        :total="totalTransactions"
        :backend-sorting="true"
        @sort="onSort"
        :per-page="transactionsPerPage"
        :current-page="currentPage"
        :loading="isLoading"
        detailed
        detail-key="id"
        detail-transition="fade"
        :aria-next-label="$t('next-page')"
        :aria-previous-label="$t('previous-page')"
        :aria-page-label="$t('page')"
        :aria-current-label="$t('current-page')">

        <b-table-column field="when" :label="$t('account.when')" v-slot="props" sortable>
          <datetime-display :asdate="true" :datetime="props.row.when"></datetime-display>
        </b-table-column>

        <b-table-column field="amount" :label="$t('amount')" v-slot="props" sortable>
          <currency-display :currency="props.row.currency" :amount="getAmountWithCurrency(props.row.amount)" :do-color="false"></currency-display>
        </b-table-column>

        <b-table-column field="category" :label="$t('category')" v-slot="props">
          <b-field class="level-item">
            <!-- icon-pack="fas" :icon="categoryMap[selectedCategories[props.row.id]].icon"  -->
            <p class="control" v-if="props.row.ml_category">
              <b-tooltip :label="$t('ml_model.reset_to_predicted')" class="is-secondary is-light">
                <b-button v-on:click="selectedCategories[props.row.id] = props.row.ml_category.id" icon-right="desktop" size="is-small" :class="getButtonClass(props.row)"></b-button>
              </b-tooltip>
            </p>
            <p class="control">
              <b-tooltip :label="conditionalSuggestedLabel(props.row.ml_category && selectedCategories[props.row.id] == props.row.ml_category.id, props.row.ml_proba)" class="is-secondary is-light">
                <b-button :icon-right="categoryMap[selectedCategories[props.row.id]].icon" size="is-small" :class="getSelectedIconClass(props.row)"></b-button>
              </b-tooltip>
            </p>
            <b-select v-model="selectedCategories[props.row.id]" size="is-small">
              <optgroup v-for="top_level in categories" :key="top_level.id" :value="top_level.id" :label="top_level.nestedName">
                <option v-for="bottom_level in top_level.children" :key="bottom_level.id" :value="bottom_level.id">
                  <p>{{bottom_level.name}}</p>
                </option>
              </optgroup>
            </b-select>
            <p class="control">
              <b-tooltip :label="$t('save')" class="is-secondary is-light">
                <b-button v-on:click="() => { saveLabel(props.row); }" icon-right="check" size="is-small" :class="getButtonClass(props.row)"></b-button>
              </b-tooltip>
            </p>
          </b-field>
        </b-table-column>

        <template #detail="props">
          <p>{{props.row.id}}</p>
        </template>
      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Category from '@/utils/api/Category';
import currency from 'currency.js'
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay.vue'
import Transaction from '@/utils/api/Transaction';
import Vue from 'vue';

export default defineComponent({
  components: { DatetimeDisplay, CurrencyDisplay },
  data() {
    return {
      transactions: [],
      transactionsPerPage: 10,
      currentPage: 1,
      isLoading: false,
      sortField: 'when',
      sortOrder: 'asc',
      totalTransactions: 0,
      selectedCategories: {},
      commitedCategories: {},
      categories: []
    }
  },
  async created() {
    this.isLoading = true;
    this.categories = await Category.getFlattenedCategoryTree();
    await this.updateTransactions();
    this.totalTransactions = await Transaction.countAll(this.getFilterParams());
    this.isLoading = false; 
  },
  computed: {
    pageStart() {
      return (this.currentPage - 1) * this.transactionsPerPage;
    },
    categoryMap() {
      let map = {};
      this.categories.map(top => {
        top.children.map(c => {
          map[c.id] = c;
        });
      });
      return map;
    }
  },
  methods: {
    getSelectedIconClass(transaction) {
      let selected = this.selectedCategories[transaction.id];
      if (this.categoryMap[selected].income) {
        return "incomeClass";
      } else {
        return "expenseClass";
      }
    },
    getButtonClass(transaction) {
      let commited = this.commitedCategories[transaction.id];
      let selected = this.selectedCategories[transaction.id];
      if (commited && commited.id == selected) {
        return "is-success";
      } else if (commited && commited.id != selected) {
        return "is-warning";
      } else {
        return "is-info";
      }
    },
    conditionalSuggestedLabel(cond, proba) {
      if (cond) {
        return this.$t('ml_model.label_suggested_by_ml', {proba: (proba * 100).toFixed(2)});
      } else {
        return this.$t('ml_model.not_suggested_by_ml');
      }
    },
    setSelectedCategories() {
      this.selectedCategories = {};
      this.transactions.forEach(transaction => {
        Vue.set(this.selectedCategories, transaction.id, !transaction.ml_category ? this.categories[0].children[0].id : transaction.ml_category.id);
        Vue.set(this.commitedCategories, transaction.id, null);
      });
    },
    getAmountWithCurrency(amount) {
      return currency(amount);
    },
    async onPageChange(page) {
      this.currentPage = page;
      this.isLoading = true;
      await this.updateTransactions();
      this.isLoading = false; 
    },
    async onSort(field, order) {
      this.sortField = field;
      this.sortOrder = order;
      this.isLoading = true;
      await this.updateTransactions();
      this.isLoading = false; 
    },
    async updateTransactions() {
      this.transactions = await this.getFilteredTransactions();
      this.setSelectedCategories();
    },
    async getFilteredTransactions() {
      return await Transaction.fetchAll(this.getPaginateParams());
    },
    getFilterParams() {
      return {
        has_category: false
      };
    },
    getPaginateParams() {
      return {
        order: this.sortOrder,        
        sort_by: this.sortField,
        count: this.transactionsPerPage,
        start: this.pageStart,
        ml_category: true,
        ... this.getFilterParams()
      };
    },
    async saveLabel(transaction) {
      let model = new Transaction(transaction);
      await model.setCategory(this.selectedCategories[model.id]);
      this.commitedCategories[model.id] = model.category; 
    }
  }
})
</script>

<style lang="scss" scoped>
@import "@/assets/colors.scss";
.expenseClass {
  color: $amount-negative;
}
.incomeClass {
  color: $amount-positive;
}
.proba {
  font-size: 0.6em;
  color: gray;
}

</style>