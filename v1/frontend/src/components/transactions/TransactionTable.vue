<template>
  <div>
    <table-with-query-filter :data="transactions" :columns="columns" :filter-from-query="queryFilter" :title="title">

      <template slot="when" slot-scope="props">
        <datetime-display :asdate="true" :datetime="props.row.when"></datetime-display>
      </template>

      <template slot="amount" slot-scope="props">
        <currency-display :currency="props.row.currency" :amount="getSignedAmount(props.row)" :do-color="!!referenceAccount"></currency-display>
      </template>

      <template slot="description" slot-scope="props">
        <b-tooltip :label="getTransactionDescription(props.row)" type="is-primary" multilined>
          <string-or-null-display :truncate="125" :value="getTransactionDescription(props.row)"></string-or-null-display>
        </b-tooltip>
      </template>

      <!-- when there is a reference account -->
      <template slot="counterpart.number" slot-scope="props" v-if="referenceAccount">
        <account-number-display :number="getCounterpartNumber(props.row)"></account-number-display>
      </template>

      <template slot="counterpart.name" slot-scope="props" v-if="referenceAccount">
        <string-or-null-display :value="getCounterpartName(props.row)"></string-or-null-display>
      </template>

      <!-- when there is no reference account -->
      <template slot="source.number" slot-scope="props" v-if="!referenceAccount">
        <account-number-display :number="props.row.source ? props.row.source.number : null"></account-number-display>
      </template>

      <template slot="source.name" slot-scope="props" v-if="!referenceAccount">
        <string-or-null-display :value="props.row.source ? props.row.source.name : null"></string-or-null-display>
      </template>

      <template slot="dest.number" slot-scope="props" v-if="!referenceAccount">
        <account-number-display :number="props.row.dest.number"></account-number-display>
      </template>

      <template slot="dest.name" slot-scope="props" v-if="!referenceAccount">
        <string-or-null-display :value="props.row.dest.name"></string-or-null-display>
      </template>

      <template slot="category" slot-scope="props">
        <category-tag :category="props.row.category"></category-tag>
      </template>

      <template slot="actions" slot-scope="props">
        <b-field grouped class="buttons">
          <!-- duplicate -->
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
      </template>

    </table-with-query-filter>
    <b-button v-if="showLoadMore" :disabled="!loadMoreEnabled" @click="loadMoreTransactions" expanded type="is-primary">{{ $t('load_more') }}</b-button>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import { queryFilter } from './TransactionTableData.js';
import { strcurrency } from '@/utils/helpers';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay';
import CategoryTag from '@/components/categories/CategoryTag';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay';
import MarkDuplicateTransactionForm from '@/components/transactions/MarkDuplicateTransactionForm';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';
import TableWithQueryFilter from '@/components/generic/TableWithQueryFilter';
import Vue from 'vue';

export default defineComponent({
  components: {
    TableWithQueryFilter,
    CurrencyDisplay,
    StringOrNullDisplay,
    CategoryTag,
    AccountNumberDisplay,
    MarkDuplicateTransactionForm,
    DatetimeDisplay
  },
  props: {
    transactions: Array,
    referenceAccount: Object,
    title: String,
    showLoadMore: { type: Boolean, default: false },
    loadMoreEnabled: { type: Boolean, default: false }
  },
  data() {
    return {
      queryFilter,
      activeDuplicateModals: {}
    }
  },
  created() {
    this.setAllDuplicateModalInactive();
  },
  computed: {
    columns() {
      let columns = [];
      columns.push({field: 'when', label: this.$t('date')});
      if (this.referenceAccount) {
        columns.push({field: 'counterpart.number', label: this.$t('account.number')});
        columns.push({field: 'counterpart.name', label: this.$t('account.name')});
      } else {
        columns.push({field: 'source.number', label: this.$t('account.source.number')});
        columns.push({field: 'source.name', label: this.$t('account.source.name')});
        columns.push({field: 'dest.number', label: this.$t('account.dest.number')});
        columns.push({field: 'dest.name', label: this.$t('account.dest.name')});
      }
      columns.push({field: 'amount', label: this.$t('amount'), numeric: true});
      columns.push({field: 'description', label: this.$t('description'), width: 600});
      columns.push({field: 'category', label: this.$t('category') });
      columns.push({field: 'actions', label: this.$t('actions')});
      return columns;
    }
  },
  watch: {
    transactions: {
      handler(newTransactions, oldTransactions) {
        if (newTransactions.length !== oldTransactions.length) {
          this.setAllDuplicateModalInactive();
        }
      },
      deep: true
    }
  },
  methods: {
    goToAccount(id) {
      this.$router.push({'name': 'view-account', params: {'accountid': id}});
    },
    setAllDuplicateModalInactive() {
      this.activeDuplicateModals = {};
      this.transactions.forEach(transaction => {
        Vue.set(this.activeDuplicateModals, transaction.id, false);
      });
    },
    getSignedAmount(t) {
      if (!!this.referenceAccount && t.source && t.source.id == this.referenceAccount.id) {
        return strcurrency(t.amount).multiply(-1);
      } else {
        return t.amount;
      }
    },
    getCounterpart(t) {
      if (!this.referenceAccount) {
        throw new Error("cannot extract counter part when there is no reference account");
      }
      if (t.id_source && this.referenceAccount.id != t.source.id) {
        return t.source;
      } else if (t.id_dest) {
        return t.dest;
      } else {
        return null;
      }
    },
    getCounterpartName(t) {
      let counterpart = this.getCounterpart(t);
      if (! counterpart) {
        return null;
      }
      return counterpart.name;
    },
    getCounterpartNumber(t) {
      let counterpart = this.getCounterpart(t);
      if (! counterpart) {
        return null;
      }
      return counterpart.number;
    },
    getTransactionDescription(t) {
      return t && t.description ? t.description : null;
    },
    loadMoreTransactions() {
      this.$emit('load-more-transactions');
    }
  }
})
</script>

<style lang="scss" scoped>

</style>