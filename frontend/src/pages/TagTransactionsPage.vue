<template>
  <div>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('tagging.title')}}</h3></div>
      <div class="level-right">
        <b-field class="level-item is-small"><b-button class="is-small" icon-right="check-circle" v-on:click="validatePage">{{$t('tagging.validate_page')}}</b-button></b-field>
        <b-field class="level-item is-small"><b-button class="is-small" icon-right="sync" v-on:click="refreshPage">{{$t('refresh')}}</b-button></b-field>
        <b-field class="level-item is-small" :label="$t('category')" label-position="on-border">
          <b-select size="is-small" v-model="globalCategory">
            <optgroup v-for="top_level in categories" :key="top_level.id" :value="top_level.id" :label="top_level.nestedName">
              <option v-for="bottom_level in top_level.children" :key="bottom_level.id" :value="bottom_level.id">
                <p>{{bottom_level.name}}</p>
              </option>
            </optgroup>
          </b-select>
          <b-button class="is-primary is-small" @click="setAllCategories" icon-right="pen">{{$t('tagging.set_all')}}</b-button>
        </b-field>
        <b-field class="level-item is-small" :label="$t('tagging.transac_per_page')" label-position="on-border">
          <b-select size="is-small" v-model="transactionsPerPage" @input="refreshPage">
            <option v-for="number in perPageNumbers" :key="number" :value="number">{{number}}</option>
          </b-select>
        </b-field>
      </div>
    </section>
      <b-collapse animation="slide" :open="false">
        <template #trigger>
          <div class="collapseHeader" role="button">
            <p class="subtitle">{{$t('transaction.filters.title')}}</p>
          </div>
        </template>
        <div class="collapseInner">
          <transactions-filter-form :clearFn="clearFormFilters" :filterFn="selectFormFilters"></transactions-filter-form>
        </div>
      </b-collapse>
    <section>
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
        
        <b-table-column :label="$t('account.source.name')" field="source.number" v-slot="props">
          <string-or-null-display :value="props.row.source.number"></string-or-null-display>
        </b-table-column>

        <b-table-column :label="$t('account.source.number')" field="source.name" v-slot="props">
          <string-or-null-display :value="props.row.source.name"></string-or-null-display>
        </b-table-column>

        <b-table-column :label="$t('account.dest.name')" field="dest.number" v-slot="props">
          <string-or-null-display :value="props.row.dest.number"></string-or-null-display>
        </b-table-column>

        <b-table-column :label="$t('account.dest.number')" field="dest.name" v-slot="props">
          <string-or-null-display :value="props.row.dest.name"></string-or-null-display>
        </b-table-column>

        <b-table-column field="amount" :label="$t('amount')" v-slot="props" sortable>
          <currency-display :currency="props.row.currency" :amount="getAmountWithCurrency(props.row.amount)" :do-color="false"></currency-display>
        </b-table-column>

        <b-table-column field="category" :label="$t('category')" v-slot="props">
          <b-field class="level-item">
            <p class="control" v-if="props.row.ml_category">
              <b-tooltip :label="$t('ml_model.reset_to_predicted')" class="is-secondary is-light">
                <b-button v-on:click="selectedCategories[props.row.id] = props.row.ml_category.id" icon-right="desktop" size="is-small" :class="getButtonClass(props.row)"></b-button>
              </b-tooltip>
            </p>
            <p class="control">
              <b-tooltip :label="props.row.id_category ? $t('tagging.current_category_is', {categName: props.row.category.name}): $t('tagging.no_category')" class="is-secondary">
                <b-button v-on:click="() => clickOnCurrentCategoryButton(props.row)"  :icon-right="getCurrentCategoryIcon(props.row)" :disabled="!props.row.id_category" size="is-small"></b-button>
              </b-tooltip>
            </p>
            <p class="control">
              <b-tooltip :label="conditionalSuggestedLabel(props.row.ml_category && selectedCategories[props.row.id] == props.row.ml_category.id, props.row.ml_proba)" class="is-secondary is-light">
                <b-button :icon-right="getSelectedIcon(props.row)" size="is-small" :class="getSelectedIconClass(props.row)"></b-button>
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

        <b-table-column field="proba" label="" v-slot="props">
          <b-tooltip v-if="props.row.ml_category" :label="`${probaToPercentage(props.row.ml_proba)} %`" class="is-secondary is-light">
            <tiny-pie-chart-icon class="probaPie" :ratio="props.row.ml_proba"></tiny-pie-chart-icon>
          </b-tooltip>
        </b-table-column>

        <template #detail="props">
          <table class="table">
            <tbody>
               <tr v-for="(value, key) in props.row.metadata_" :key="key" :value="value">
                <th>{{humanReadable(key)}}</th>
                <td>{{value}}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </b-table>
    </section>
  </div>
</template>

<script>
import Vue from 'vue';
import Transaction from '@/utils/api/Transaction';
import TinyPieChartIcon from '../components/icons/TinyPieChartIcon';
import StringOrNullDisplay from '../components/generic/StringOrNullDisplay';
import TransactionsFilterForm from '../components/transactions/TransactionsFilterForm';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay'
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import Category from '@/utils/api/Category';
import { strcurrency } from '@/utils/helpers';
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  components: { DatetimeDisplay, CurrencyDisplay, StringOrNullDisplay, TinyPieChartIcon, TransactionsFilterForm },
  name: "TagTransactionPage",
  data() {
    return {
      transactions: [],
      transactionsPerPage: 25,
      currentPage: 1,
      isLoading: false,
      sortField: 'when',
      sortOrder: 'desc',
      formFilters: null, 
      totalTransactions: 0,
      globalCategory: null,
      selectedCategories: {},
      commitedCategories: {},
      categories: [],
      perPageNumbers: [5, 10, 25, 50, 100],
    }
  },
  async created() {
    this.isLoading = true;
    this.categories = await Category.getFlattenedCategoryTree();
    await this.updateTransactions();
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
    humanReadable(s) {
      if (s) {
        return (s.charAt(0).toUpperCase() + s.slice(1)).replaceAll("_", " ");        
      } else {
        return "";
      }
    },
    getSelectedIcon(transaction) {
      let selected = this.selectedCategories[transaction.id];
      if (!selected || !this.categoryMap[selected]) {
        return "";
      }
      return this.categoryMap[selected].icon;
    },
    getCurrentCategoryIcon(transaction) {
      if (transaction.id_category) {
        return transaction.category.icon;
      } else {
        return 'times';
      }
    },
    getSelectedIconClass(transaction) {
      let selected = this.selectedCategories[transaction.id];
      if (!selected || !this.categoryMap[selected]) {
        return "";
      }
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
        return this.$t('ml_model.label_suggested_by_ml', {proba: this.probaToPercentage(proba)});
      } else {
        return this.$t('ml_model.not_suggested_by_ml');
      }
    },
    probaToPercentage(proba) {
      return (proba * 100).toFixed(2);
    },
    setSelectedCategories() {
      this.selectedCategories = {};
      let defaultCategory = this.categories[0].children[0].id;
      this.transactions.forEach(transaction => {
        let category = defaultCategory;
        if (transaction.ml_category) {
          category = transaction.ml_category.id;
        } else if (transaction.category) {
          category = transaction.category.id;
        }
        Vue.set(this.selectedCategories, transaction.id, category);
        Vue.set(this.commitedCategories, transaction.id, null);
      });
    },
    getAmountWithCurrency(amount) {
      return strcurrency(amount);
    },
    async onPageChange(page) {
      this.currentPage = page;
      await this.updateTransactionsWithLoading();
    },
    async onSort(field, order) {
      this.sortField = field;
      this.sortOrder = order;
      await this.updateTransactionsWithLoading();
    },
    async updateTransactionsWithLoading() {
      this.isLoading = true;
      await this.updateTransactions();
      this.isLoading = false; 
    },
    async updateTransactions() {
      this.transactions = await this.getFilteredTransactions();
      this.totalTransactions = await Transaction.countAll(this.getAllParams());
      this.setSelectedCategories();
    },
    async getFilteredTransactions() { 
      return await Transaction.fetchAll(this.getAllParams());
    },
    getAllParams() {
      return {...this.getFilterParams(), ...this.getPaginateParams()};
    },
    getFilterParams() {
      return {
        ...this.formFiltersForApi()
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
      let categoryId = this.selectedCategories[model.id];
      await model.setCategory(categoryId);
      this.commitedCategories[model.id] = model.category; 
      transaction.id_category = categoryId;
      transaction.category = this.categoryMap[categoryId];
    },
    async refreshPage() {
      await this.updateTransactionsWithLoading();
    },
    async validatePage() {
      let transactions = this.transactions.map(t => {
        return {id_transaction: t.id, id_category: this.selectedCategories[t.id]};
      });
      await Transaction.setCategories(transactions);
      await this.refreshPage();
    },
    setAllCategories() {
      this.transactions.map(t => {
        this.selectedCategories[t.id] = this.globalCategory;
      });
    },
    async selectFormFilters(filters) {
      this.formFilters = filters;
      await this.updateTransactionsWithLoading();
    },
    async clearFormFilters() {
      let needsRefresh = !!this.formFilters; 
      this.formFilters = null;
      if (needsRefresh) {
        await this.updateTransactionsWithLoading();
      }
    },
    clickOnCurrentCategoryButton(transaction) {
      if (transaction.id_category) {
        this.selectedCategories[transaction.id] = transaction.id_category;
      }
    },
    formFiltersForApi() {
      let filters = {labeled: false};
      if (!this.formFilters) {
        return filters;
      }
      if (this.formFilters.accountTo) {
        filters.account_to = this.formFilters.accountTo.id;
      }
      if (this.formFilters.accountFrom) {
        filters.account_from = this.formFilters.accountFrom.id;
      }
      if (this.formFilters.periodFrom) {
        filters.date_from = this.formFilters.periodFrom.format("YYYY-MM-DD");
      }
      if (this.formFilters.periodTo) {
        filters.date_to = this.formFilters.periodTo.format("YYYY-MM-DD");
      }
      if (this.formFilters.category) {
        filters.labeled = this.formFilters.category;
      } else if (this.formFilters.includeLabeled) {
        filters.labeled = undefined;
      }
      if (this.formFilters.amountFrom) {
        filters.amount_from = this.formFilters.amountFrom;
      }
      if (this.formFilters.amountTo) {
        filters.amount_to = this.formFilters.amountTo;
      }
      return filters;
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
.probaPie {
  margin-top: 3px;
}
section {
  margin-bottom: 10px;
}
.collapseInner {
  padding: 10px;
  background-color: $placeholder;
  border: 1px solid rgba(0, 0, 0, .1);;
}
.collapseHeader {
  background-color: $primary;
  padding: 5px;
  padding-left: 10px;
  border-radius: 5px 5px 0px 0px;
}
.collapseHeader > .subtitle {
  color: $primary-invert;
}
.collapse {
  margin-bottom: 10px;
}
</style>