<template>
  <div>
    <b-field :label="fieldTitle" label-position="on-border">
      <b-autocomplete 
        clearable 
        v-model="query" 
        :data="filteredData" 
        @select="handleSelection"
        :custom-formatter="formatEntry"
        ref="autocomplete">
      </b-autocomplete>
    </b-field>
    <account-alias-table :aliases="getAliases(value)" :title="$t('account.aliases')"></account-alias-table>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import { queryFilter } from '@/components/accounts/AccountAliasTableData';
import AccountAliasTable from './AccountAliasTable.vue';

export default defineComponent({
  components: { AccountAliasTable },
  props: {
    accounts: Array,
    fieldTitle: String,
    value: Object,
  },
  data() {
    return {
      query: '',
      selected: this.value
    };
  },  
  computed: {
    filteredData() {
      return queryFilter(this.query, this.accounts, true);
    }
  },
  methods: {
    formatEntry(e) {
      let formatted = '';
      formatted += e.name ? e.name : this.$t('undefined');
      formatted += " - ";
      formatted += e.number ? e.number : this.$t('undefined');
      return formatted;
    },
    getAliases(account) {
      if (!account) {
        return [];
      }
      return account.equivalences;
    },
    handleSelection(value) {
      this.selected = value;
      this.$emit('input', this.selected)
    }
  },
  watch: {
    // needed for two-ways binding ??? 
    value: function(newValue) {
      if (!newValue && !!this.selected) {
        this.query = '';  // reset autocomplete
      } else if (this.selected != newValue) {
        this.$refs.autocomplete.setSelected(newValue);  // select the new value
      }
    }
  }
})
</script>

<style lang="scss" scoped>

</style>