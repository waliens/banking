<template>
  <table-with-query-filter
    :columns="columns"
    :data="aliases"
    :query-filter="queryFilter"
    :title="title">
  </table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '../generic/TableWithQueryFilter.vue';
import { getColumns, queryFilter } from '@/components/accounts/AccountAliasTableData';

export default defineComponent({
  components: { TableWithQueryFilter },
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