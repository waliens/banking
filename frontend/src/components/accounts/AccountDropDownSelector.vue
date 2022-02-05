<template>
  <b-field :label="fieldTitle" label-position="on-border">
    <b-autocomplete 
      clearable 
      v-model="query" 
      :data="filteredData" 
      @select="handleSelection"
      :custom-formatter="formatEntry"
      ref="autocomplete"
      expanded>
    </b-autocomplete>
    <p class="control"><b-button @click="goToAccount" :disabled="!selected" icon-left="eye" class="is-secondary"></b-button></p>
  </b-field>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import { queryFilter } from '@/components/accounts/AccountTableData';
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
      return e.formatName(this);
    },
    handleSelection(value) {
      this.selected = value;
      this.$emit('input', this.selected)
    },
    goToAccount(accountId) {
      if (this.selected) {
        this.$router.push({ name: 'view-account', params: {accountId}});
      }
    }
  },
  watch: {
    // needed for two-ways binding apparently
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