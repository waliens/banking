<template>
  <table-with-query-filter :data="accounts" :columns="columns" :filter-from-query="queryFilter" :title="title">

    <template slot="balance" slot-scope="props">
      <currency-display :currency="props.row.currency" :amount="props.row.balance" :color="false"></currency-display>
    </template>

    <template slot="explore" slot-scope="props">
      <b-field grouped>
        <b-button class="is-small is-primary" icon-right="eye" v-on:click="goToAccount(props.row.id)"></b-button>
      </b-field>
    </template>

  </table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '@/components/generic/TableWithQueryFilter';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import { getColumns, queryFilter } from './AccountTableData.js';

export default defineComponent({
  components: { TableWithQueryFilter, CurrencyDisplay },
  props: { accounts: Array, title: String },
  data() {
    return {
      columns: getColumns(this),
      queryFilter
    }
  },
  methods: {
    goToAccount(id) {
      this.$router.push({'name': 'view-account', params: {'accountid': id}});
    }
  }
})
</script>

<style lang="scss" scoped>
</style>