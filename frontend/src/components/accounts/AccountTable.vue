<template>
  <table-with-query-filter :columns="columns" :data="accounts" :filter-from-query="queryFilter"></table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '@/components/generic/TableWithQueryFilter';
import { getColumns, queryFilter } from './AccountTableData.js';

export default defineComponent({
  components: { TableWithQueryFilter },
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