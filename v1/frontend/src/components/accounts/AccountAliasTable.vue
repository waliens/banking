<template>
  <table-with-query-filter
    :columns="columns"
    :data="aliases"
    :filter-from-query="queryFilter"
    :title="title">
    
    <template slot="number" slot-scope="props">
      <account-number-display :number="props.row.number"></account-number-display>
    </template>

    <template slot="name" slot-scope="props">
      <string-or-null-display :value="props.row.name"></string-or-null-display>
    </template>

  </table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '../generic/TableWithQueryFilter.vue';
import { getColumns, queryFilter } from '@/components/accounts/AccountAliasTableData';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';

export default defineComponent({
  components: { TableWithQueryFilter, AccountNumberDisplay, StringOrNullDisplay },
  props: {
    aliases: Array,
    title: String
  },
  data() {
    return {
      queryFilter,
      columns: getColumns(this)
    };
  }
})
</script>

<style lang="scss" scoped>

</style>