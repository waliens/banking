<template>
  <b-table :data="accounts" :columns="columns"></b-table>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
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
})
</script>

<style lang="scss" scoped>

</style>