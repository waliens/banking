<template>
  <table-with-query-filter :data="transactions" :columns="columns" :filter-from-query="queryFilter" :title="title">

    <template slot="amount" slot-scope="props">
      <currency-display :currency="props.row.currency" :amount="getSignedAmount(props.row)" :do-color="!!referenceAccount"></currency-display>
    </template>

    <template slot="description" slot-scope="props">
      <string-or-null-display :truncate="75" :value="getTransactionDescription(props.row)"></string-or-null-display>
    </template>

    <!-- when there is a reference account -->
    <template slot="conterpart.number" slot-scope="props" v-if="referenceAccount">
      <account-number-display :number="getCounterpartNumber(props.row)"></account-number-display>
    </template>

    <template slot="conterpart.name" slot-scope="props" v-if="referenceAccount">
      <string-or-null-display :value="getCounterpartName(props.row)"></string-or-null-display>
    </template>
    
    <!-- when there is no reference account -->
    <template slot="source.number" slot-scope="props" v-if="!referenceAccount">
      <account-number-display :number="props.row.source.number"></account-number-display>
    </template>

    <template slot="source.name" slot-scope="props" v-if="!referenceAccount">
      <string-or-null-display :value="props.row.source.name"></string-or-null-display>
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

  </table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '@/components/generic/TableWithQueryFilter';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';
  import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay';
import CategoryTag from '@/components/categories/CategoryTag';
import { queryFilter } from './TransactionTableData.js';
import { strcurrency } from '@/utils/helpers';

export default defineComponent({
  components: { TableWithQueryFilter, CurrencyDisplay, StringOrNullDisplay, CategoryTag, AccountNumberDisplay },
  props: { transactions: Array, referenceAccount: Object, title: String },
  data() {
    return {
      queryFilter
    }
  },
  computed: {
    columns() {
      let columns = [];
      columns.push({field: 'when', label: this.$t('date')});
      if (this.referenceAccount) {
        columns.push({field: 'conterpart.number', label: this.$t('account.number')});
        columns.push({field: 'conterpart.name', label: this.$t('account.name')});
      } else {
        columns.push({field: 'source.number', label: this.$t('account.source.number')});
        columns.push({field: 'source.name', label: this.$t('account.source.name')});
        columns.push({field: 'dest.number', label: this.$t('account.dest.number')});
        columns.push({field: 'dest.name', label: this.$t('account.dest.name')});
      }
      columns.push({field: 'amount', label: this.$t('amount'), numeric: true});
      columns.push({field: 'description', label: this.$t('description'), width: 400});
      columns.push({field: 'category', label: this.$t('category') });
      return columns;
    }
  },
  methods: {
    goToAccount(id) {
      this.$router.push({'name': 'view-account', params: {'accountid': id}});
    },
    getSignedAmount(t) {
      if (!!this.referenceAccount && t.source.id == this.referenceAccount.id) {
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
      if (t && t.metadata_ && Object.prototype.hasOwnProperty.call(t.metadata_, 'transaction')) {
        let desc = new String(t.metadata_['transaction']);
        if (desc.length > 0) {
          return desc;
        }
      }
      return null;
    }
  }
})
</script>

<style lang="scss" scoped>

</style>