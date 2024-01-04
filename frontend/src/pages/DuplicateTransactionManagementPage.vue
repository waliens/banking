<!-- can you generate an empty vue2 component -->
<template>
  <div>
    <section>
      <b-loading :is-full-page="false" :active="loading"/>
      <h3 class="title">{{ $t('navbar.manage_duplicate') }}</h3>
    </section>
    <section>
      <b-collapse
        class="card"
        animation="slide"
        v-model="isOpen">
        <template #trigger>
          <div
            class="card-header has-background-primary"
            role="button"
            :aria-expanded="isOpen">
            <p class="card-header-title filter-title">{{$t('transaction.filters.title')}}</p>
          </div>
        </template>
        <div class="card-content">
          <transactions-filter-form :clearFn="clearFormFilters" :filterFn="selectFormFilters" :enable-group-filters="false"></transactions-filter-form>
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
            <b-tooltip :label="$t('transaction.duplicate.unduplicate.tooltip')" class="is-danger" position="is-left">
              <b-button icon-left="times" class="is-danger is-small" @click="unduplicate(props.row)" />
            </b-tooltip>
          </b-field>
        </b-table-column>

        <template #detail="props">
          <duplicate-comparison-table :duplicate-transaction="props.row" />
        </template>
      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Transaction from '@/utils/api/Transaction';
import TransactionsFilterForm from '@/components/transactions/TransactionsFilterForm.vue';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay.vue';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay.vue';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay.vue';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay.vue';
import { strcurrency } from '@/utils/helpers';
import DuplicateComparisonTable from '@/components/transactions/DuplicateComparisonTable';


export default defineComponent({
  components: {
    DatetimeDisplay,
    CurrencyDisplay,
    StringOrNullDisplay,
    TransactionsFilterForm,
    AccountNumberDisplay,
    DuplicateComparisonTable
  },
  data() {
    return {
      loading: false, // page loading
      transactions: [],
      transactionsPerPage: 25,
      currentPage: 1,
      totalTransactions: 0,
      isLoading: false, // table loading
      isOpen: false,
      sortField: 'when',
      sortOrder: 'desc'
    }
  },
  async created() {
    this.loading = true;
    await this.updateTransactionsWithLoading();
    this.loading = false;
  },
  methods: {
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
    formFiltersForApi() {
      let filters = {
        duplicate_only: true,
        labeled: false
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
      return filters;
    },
    getAmountWithCurrency(amount) {
      return strcurrency(amount);
    },
    async unduplicate(transaction) {
      await transaction.markAsNotDuplicate().then(() => {
        this.$buefy.toast.open({
          message: this.$t('transaction.duplicate.unduplicate.success'),
          type: 'is-success'
        });
        this.updateTransactionsWithLoading();
      }).catch(() => {
        this.$buefy.toast.open({
          message: this.$t('transaction.duplicate.unduplicate.error'),
          type: 'is-danger'
        });
        this.updateTransactionsWithLoading();
      })

    }
  }
})
</script>

<style lang="scss" scoped>
.filter-title {
  color: white;
}
</style>