<template>
  <table-with-query-filter :data="accounts" :columns="columns" :filter-from-query="queryFilter">

    <template slot="balance" slot-scope="props">
      <currency-display :currency="props.row.currency" :amount="props.row.balance" :color="false"></currency-display>
    </template>

    <template slot="explore" >
      <b-field grouped>
        <button>go</button>
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
  props: { 'accounts': Array },
  data() {
    return {
      columns: getColumns(this),
      queryFilter
    }
  }
})
</script>

<style lang="scss" scoped>

</style>