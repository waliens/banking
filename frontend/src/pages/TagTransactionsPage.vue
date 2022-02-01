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

          <template #detail="props">
            <p>{{props.row.id}}</p>
          </template>
      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import DatetimeDisplay from '@/components/generic/DatetimeDisplay.vue'
import currency from 'currency.js'
import Transaction from '@/utils/api/Transaction';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';

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
      totalTransactions: 0
    }
  },
  async created() {
    this.isLoading = true;
    await this.updateTransactions();
    this.totalTransactions = await Transaction.countAll(this.getFilterParams());
    this.isLoading = false; 
  },
  computed: {
    pageStart() {
      return (this.currentPage - 1) * this.transactionsPerPage;
    }
  },
  methods: {
    getAmountWithCurrency(amount) {
      return currency(amount);
    },
    async onPageChange(page) {
      this.currentPage = page;
      await this.updateTransactions();
    },
    async onSort(field, order) {
      this.sortField = field;
      this.sortOrder = order;
      await this.updateTransactions();
    },
    async updateTransactions() {
      this.isLoading = true;
      this.transactions = await this.getFilteredTransactions();
      this.isLoading = false;
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
    }
  }
})
</script>

<style lang="sass" scoped>

</style>