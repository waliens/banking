<template>
  <div v-if="account">
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('account.edit')}}</h3></div>
      <div class="level-left"> <b-button v-on:click="save" class="level-item is-small" icon-right="save">{{$t('save')}}</b-button></div>
    </section>
    <section class="form">
      <b-field :label="$t('account.number')" label-position="on-border">
        <b-input v-model="account.number" disabled></b-input>
      </b-field>
      <b-field :label="$t('account.name')" label-position="on-border">
        <b-input v-model="account.name" disabled></b-input>
      </b-field>
      <b-field :label="$t('account.initial')" label-position="on-border">
        <b-input v-model="initial" :icon-right="Currency.currency2icon(account.currency)"></b-input>
      </b-field>
      <double-table-select
          :data="allAliases"
          :selected.sync="selected"
          :keyFn="getAliasKey"
          :filterFromQuery="queryFilter"
          :columns="columns"
          :title-selected="$t('account.representative')"
          :title-not-selected="$t('account.aliases')"
          :max-selected="1">

      </double-table-select>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Account from '@/utils/api/Account';
import DoubleTableSelect from '../components/generic/DoubleTableSelect.vue';
import Currency from '@/utils/api/Currency';
import { queryFilter, getColumns } from '@/components/accounts/AccountAliasTableData';

export default defineComponent({
  components: { DoubleTableSelect },
  data() {
    return {
      queryFilter,
      Currency,
      account: null,
      representative: null,
      selected: [],
      initial: new Number(),
      columns: getColumns(this)
    };
  },
  async created() {
    this.account = await this.fetchAccount();
    this.representative = this.makeAliasFromAccount(this.account);
    this.selected = [this.representative];
    this.initial = new Number(this.account.initial);
  },
  computed: {
    accountId() {
      return this.$route.params.accountId;
    },
    allAliases() {
      let all = new Array();
      all = all.concat(this.account.aliases)
      all.push(this.makeAliasFromAccount(this.account));
      return all;
    }
  },
  methods: {
    async fetchAccount() {
      return await new Account({id: this.accountId}).fetch();
    },
    makeAliasFromAccount(account) {
      return {
        id: -1, 
        id_account: account.id, 
        name: account.name, 
        number: account.number 
      };
    },
    getAliasKey(alias) {
      return alias.id;
    },
    async save() {
      await this.account.updateChange({
        representative: this.selected.length > 0 ? this.selected[0] : undefined,
        initial: this.initial
      });
      this.$router.push({name: 'view-account', params: {accountId: this.accountId}});
    }
  }
})
</script>

<style lang="scss" scoped>
section {
  margin-bottom: 10px;
} 
</style>