<template>
  <table-with-query-filter :columns="columns" :data="accounts" :filter_from_query="this.filter_query"></table-with-query-filter>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import TableWithQueryFilter from '../generic/TableWithQueryFilter.vue';

export default defineComponent({
  components: { TableWithQueryFilter },
  props: { 'accounts': Array },
  data() {
    return {
      columns: [
        {
          'field': 'number',
          'label': this.$t('account.number'),
          'sortable': true  
        },
        {
          'field': 'name',
          'label': this.$t('account.name'),
          'sortable': true
        },
        {
          'field': 'balance',
          'label': this.$t('account.balance'),
          'numeric': true
        }
      ]
    }
  },
  methods: {
    filter_query: function(query, data) {
      return data.filter(account => {
        let q = '/.*' + query + ' .*/g';
        return !!((account.number && account.number.match(q)
                   || account.name && account.name.match(q)))
      });
    }
  }
})
</script>

<style lang="scss" scoped>

</style>