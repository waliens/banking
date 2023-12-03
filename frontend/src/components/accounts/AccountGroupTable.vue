<template>
  <table-with-query-filter :data="accountGroups" :columns="columns" :filter-from-query="queryFilter" :title="title">
    
    <template slot="number" slot-scope="props">
      <string-or-null-display :value="props.row.account.number"></string-or-null-display>
    </template>

    <template slot="name" slot-scope="props">
      <string-or-null-display :value="props.row.account.name"></string-or-null-display>
    </template>

    <template slot="balance" slot-scope="props">
      <currency-display :currency="props.row.account.currency" :amount="props.row.account.balance" :color="false"></currency-display>
    </template>

    <template slot="contribution_ratio" slot-scope="props">
      <span v-if="props.row.contribution_ratio">{{100 * props.row.contribution_ratio}} %</span>
      <span v-else class="tag">{{$t('undefined')}}</span>
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
  import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';
  import { getColumns, queryFilter } from './AccountGroupTableData.js';
  
  export default defineComponent({
    components: { TableWithQueryFilter, CurrencyDisplay, StringOrNullDisplay },
    props: { accountGroups: Array, title: String },
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