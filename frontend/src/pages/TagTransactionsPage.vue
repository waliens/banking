<template>
  <div>
    <section v-if="!groupSelected">
      <b-message
        :has-icon="true"
        icon="info-circle"
        icon-size="small"
        :title="$t('account_group.errors.not_selected.title')"
        type="is-danger"
      >
        {{$t('account_group.errors.not_selected.message')}}
      </b-message>
    </section>
    <div v-else>
      <section class="level title-section" >
        <div class="level-left"><h3 class="level-item title">{{$t('tagging.title')}}</h3></div>
        <b-field grouped class="level-right">
          <b-field class="level-item is-small"><b-button class="is-small" icon-right="link" type="is-info" v-on:click="linkAll">{{$t('tagging.link_all')}}</b-button></b-field>
          <b-field class="level-item is-small"><b-button class="is-small" icon-right="unlink" type="is-warning" v-on:click="unlinkAll">{{$t('tagging.unlink_all')}}</b-button></b-field>
          <b-field class="level-item is-small"><b-button class="is-small" icon-right="check-circle" v-on:click="validatePage">{{$t('tagging.validate_page')}}</b-button></b-field>
          <b-field class="level-item is-small"><b-button class="is-small" icon-right="sync" v-on:click="refreshPage">{{$t('refresh')}}</b-button></b-field>
          <b-field class="level-item is-small" :label="$t('category')" label-position="on-border">
            <category-selector v-model="globalCategory" :categories="categories" size="is-small"></category-selector>
            <b-button class="is-primary is-small" @click="setAllCategories" icon-right="pen">{{$t('tagging.set_all')}}</b-button>
          </b-field>
          <b-field class="level-item is-small" :label="$t('tagging.transac_per_page')" label-position="on-border">
            <b-select size="is-small" v-model="transactionsPerPage" @input="refreshPage">
              <option v-for="number in perPageNumbers" :key="number" :value="number">{{number}}</option>
            </b-select>
          </b-field>
        </b-field>
      </section >
      <section>
        <b-collapse
          class="card"
          animation="slide"
          v-model="isFiltersFormOpen">
          <template #trigger>
            <div
              class="card-header has-background-light"
              role="button"
              :aria-expanded="isFiltersFormOpen">
              <p class="card-header-title filter-title">{{$t('transaction.filters.title')}}</p>
            </div>
          </template>
          <div class="card-content">
            <transactions-filter-form :clearFn="clearFormFilters" :filterFn="selectFormFilters"></transactions-filter-form>
          </div>
        </b-collapse>
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

          <b-table-column :label="$t('account.source.number')" field="source.number" v-slot="props">
            <account-number-display :number="props.row.source ? props.row.source.number : null"></account-number-display>
          </b-table-column>

          <b-table-column :label="$t('account.source.name')" field="source.name" v-slot="props">
            <string-or-null-display :value="props.row.source ? props.row.source.name : null"></string-or-null-display>
          </b-table-column>

          <b-table-column :label="$t('account.dest.number')" field="dest.number" v-slot="props">
            <account-number-display :number="props.row.dest ? props.row.dest.number : null"></account-number-display>
          </b-table-column>

          <b-table-column :label="$t('account.dest.name')" field="dest.name" v-slot="props">
            <string-or-null-display :value="props.row.dest ? props.row.dest.name : null"></string-or-null-display>
          </b-table-column>

          <b-table-column field="amount" :label="$t('amount')" v-slot="props" sortable>
            <currency-display :currency="props.row.currency" :amount="getAmountWithCurrency(props.row.amount)" :do-color="false"></currency-display>
          </b-table-column>

          <b-table-column :label="$t('actions')" v-slot="props">
            <b-field grouped class="buttons">
              <!-- data source -->
              <div>
                <b-tooltip :label="$t('transaction.source_to_edit', {'source': props.row.data_source})" type="is-info">
                  <b-button
                    class="is-small"
                    type="is-info"
                    :icon-left="props.row.data_source == 'manual' ? 'hand-paper' : 'upload'"
                    @click="$router.push({name: 'edit-transaction', params: {transactionid: props.row.id}})"
                    :disabled="props.row.data_source != 'manual'" />
                </b-tooltip>
              </div>
              <!-- group -->
              <div class="button-in-bar">
                <b-tooltip
                  :label="props.row.in_group ? $t('account_group.in_group_tooltip') : $t('account_group.not_in_group_tooltip')"
                  :type="props.row.in_group ? 'is-info' : 'is-warning' "
                >
                  <b-button
                    :icon-right="props.row.in_group ? 'link' : 'unlink'"
                    :type="props.row.in_group ? 'is-info' : 'is-warning'"
                    class="is-small"
                    @click="() => { updateGroupLink(props.row); }"
                  />
                </b-tooltip>
              </div>
              <!-- duplicate TODO -->
              <div class="button-in-bar">
                <b-tooltip :label="$t('transaction.duplicate.mark.title')" type="is-info">
                  <b-button
                    icon-right="copy"
                    type="is-info"
                    class="is-small"
                    @click="activeDuplicateModals[props.row.id] = true"
                  />
                </b-tooltip>

                <b-modal
                  :active.sync="activeDuplicateModals[props.row.id]"
                  has-modal-card
                  trap-focus
                  :destroy-on-hide="false">
                  <template #default="modalProps">
                    <mark-duplicate-transaction-form
                      :candidate-transaction="props.row" @close="modalProps.close" />
                  </template>
                </b-modal>

              </div>
            </b-field>
          </b-table-column>

          <!-- hidden for now because no interaction possible with transaction ratio
          <b-table-column field="group_options" :label="$t('account_group.tag')" v-slot="props">
            <div class="level">

              <div class="level-item group-info-level-item" v-if="props.row.contribution_ratio">
                <b-tooltip :label="$t('account_group.individual_contribution_ratio_tooltip')">
                  <b-tag type="is-info">{{100 * props.row.contribution_ratio}} %</b-tag>
                </b-tooltip>
              </div>
            </div>
          </b-table-column>
          -->

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
              <category-selector v-model="selectedCategories[props.row.id]" :categories="categories" size="is-small"></category-selector>
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

          <template #empty>
            <p class="no-data">{{$t('charts.no_data')}}</p>
          </template>
        </b-table>
      </section>
    </div>
  </div>
</template>

<script>
import Vue from 'vue';
import Transaction from '@/utils/api/Transaction';
import TinyPieChartIcon from '../components/icons/TinyPieChartIcon';
import StringOrNullDisplay from '../components/generic/StringOrNullDisplay';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay';
import MarkDuplicateTransactionForm from '../components/transactions/MarkDuplicateTransactionForm';
import TransactionsFilterForm from '../components/transactions/TransactionsFilterForm';
import CategorySelector from '../components/categories/CategorySelector';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay'
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import Category from '@/utils/api/Category';
import Group from '@/utils/api/Group';
import { strcurrency } from '@/utils/helpers';
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  components: {
    DatetimeDisplay,
    CurrencyDisplay,
    StringOrNullDisplay,
    TinyPieChartIcon,
    TransactionsFilterForm,
    CategorySelector,
    AccountNumberDisplay,
    MarkDuplicateTransactionForm
  },
  name: "TagTransactionPage",
  data() {
    return {
      transactions: [],
      transactionsPerPage: 25,
      currentPage: 1,
      isLoading: false,
      sortField: 'when',
      sortOrder: 'desc',
      isFiltersFormOpen: false,
      formFilters: null,
      totalTransactions: 0,
      globalCategory: null,
      selectedCategories: {},
      commitedCategories: {},
      categories: [],
      activeDuplicateModals: {},
      perPageNumbers: [5, 10, 25, 50, 100],
    }
  },
  async created() {
    if (this.groupSelected) {
      this.isLoading = true;
      this.categories = await Category.getFlattenedCategoryTree();
      await this.updateTransactions();
      this.isLoading = false;
    }
  },
  computed: {
    groupSelected() {
      return !!this.$store.state.currentGroup;
    },
    currentGroup() {
      return this.$store.state.currentGroup;
    },
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
      if (!this.groupSelected || !selected || !this.categoryMap[selected]) {
        return "";
      }
      // group contribution ratio for source and target 
      let sourceRatio = 0.0, destRatio = 0.0;
      let accountGroup = this.currentGroup;
      accountGroup.account_groups.forEach(ag => {
        if (ag.id_account == transaction.id_source) {
          sourceRatio = ag.contribution_ratio;
        }
        if (ag.id_account == transaction.id_dest) {
          destRatio = ag.contribution_ratio;
        }
      });

      if (sourceRatio > destRatio) {
        return "expenseClass";
      } else {
        return "incomeClass";
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
    setAllDuplicateModalInactive() {
      this.activeDuplicateModals = {};
      this.transactions.forEach(transaction => {
        Vue.set(this.activeDuplicateModals, transaction.id, false);
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
      this.setAllDuplicateModalInactive();
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
    /** LINK with GROUPS */
    resetTransactionForUnlink(transaction) {
      transaction.in_group = false;
      transaction.contribution_ratio = null;
    },
    resetTransactionForLink(transaction) {
      transaction.in_group = true;
      transaction.contribution_ratio = 1.0;
    },
    async updateGroupLink(transaction) {
      let currentGroup = new Group({id: this.$store.state.currentGroup.id});
      if (transaction.in_group) {
        await currentGroup.unlinkTransactions([transaction.id]).then(() => {
          this.resetTransactionForUnlink(transaction);
        });
      } else {
        await currentGroup.linkTransactions([transaction.id]).then(() => {
          this.resetTransactionForLink(transaction);
        });
      }
    },
    async unlinkAll() {
      let currentGroup = new Group({id: this.$store.state.currentGroup.id});
      await currentGroup.unlinkTransactions(this.transactions.map(t => t.id)).then(() => {
        this.transactions.forEach(t => {
          this.resetTransactionForUnlink(t);
        })
      });
    },
    async linkAll() {
      let currentGroup = new Group({id: this.$store.state.currentGroup.id});
      await currentGroup.linkTransactions(this.transactions.map(t => t.id)).then(() => {
        this.transactions.forEach(t => {
          this.resetTransactionForLink(t);
        })
      });
    },
    /** **************** */
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
      let filters = {
        labeled: false,
        group_data: true,
        group: this.$store.state.currentGroup.id,
        group_external_only: true
      };
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
      if (this.formFilters.keepCurrentGroup) {
        switch(this.formFilters.keepCurrentGroup) {
          case "only_in_group":
            // same as default
            break;
          case "only_out_group":
            filters.in_group = 0;
            break;
          case "both_in_out_group":
            filters.in_group = -1;
            break;
        }
      }
      if (this.formFilters.includeIntraGroup) {
        filters.group_external_only = false;
      }
      if (this.formFilters.queryString) {
        filters.search_query = this.formFilters.queryString;
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

.group-info-level-item {
  margin-left: 2px;
}

.button-in-bar {
  margin-left: 5px;
}


.no-data {
  text-align: center;
}
</style>