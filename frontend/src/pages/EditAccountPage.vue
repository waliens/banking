<template>
  <div v-if="account">
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('account.edit')}}</h3></div>
      <div class="level-right">
        <b-button v-on:click="openNewAliasModal" class="level-item is-small" icon-right="plus">{{$t('account.add_alias')}}</b-button>
        <b-button v-on:click="save" class="level-item is-small is-primary" icon-right="save">{{$t('save')}}</b-button>
      </div>
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

      <b-modal
        :active="newAliasModalActive"
        has-modal-card
        trap-focus
        :destroy-on-hide="false">
        <template #default>
          <div class="modal-card" style="width: auto">
            <header class="modal-card-head">
              <p class="modal-card-title">{{$t('account.new_alias')}}</p>
            </header>
            <section class="modal-card-body">
              <b-field grouped>
                <b-field :label="$t('account.alias_name')" expanded label-position="on-border"><b-input :disabled="!modalAliasAccountNameEnabled" v-model="modalAliasAccountName"></b-input></b-field>
                <b-field><b-checkbox v-model="modalAliasAccountNameEnabled" @input="aliasNameChkBoxChange"></b-checkbox></b-field>
              </b-field>
              <b-field grouped>
                <b-field :label="$t('account.alias_number')" expanded label-position="on-border"><b-input :disabled="hasAccountNumber || !modalAliasAccountNumberEnabled" v-model="modalAliasAccountNumber"></b-input></b-field>
                <b-field><b-checkbox :disabled="hasAccountNumber" v-model="modalAliasAccountNumberEnabled" @input="aliasNumberChkBoxChange"></b-checkbox></b-field>
              </b-field>
            </section>
            <footer class="modal-card-foot">
                <b-button icon-right="times" class="is-danger is-small" @click="closeModal">{{$t('cancel')}}</b-button>
                <b-button icon-right="plus" class="is-primary is-small" @click="addAlias">{{$t('create')}}</b-button>
            </footer>
          </div>
        </template>
      </b-modal>
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
      newAliasModalActive: false,
      modalAliasAccountName: null,
      modalAliasAccountNumber: null,
      modalAliasAccountNameEnabled: true,
      modalAliasAccountNumberEnabled: true,
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
    await this.refreshAccount();
    this.representative = this.makeAliasFromAccount(this.account);
    this.selected = [this.representative];
    this.initial = new Number(this.account.initial);
    this.modalAliasAccountNumber = this.accountNumber;
    this.modalAliasAccountNumberEnabled = !this.hasAccountNumber;
  },
  computed: {
    accountId() {
      return this.$route.params.accountid;
    },
    allAliases() {
      let all = new Array();
      all = all.concat(this.account.aliases)
      all.push(this.makeAliasFromAccount(this.account));
      return all;
    },
    accountNumber() {
      if (!this.account) {
        return null;
      }
      if (this.account.number) {
        return this.account.number;
      }
      if (this.account.aliases.length > 0) {
        let filtered = this.account.aliases.map(a => a.number).filter(a => !!a);
        if (filtered.length > 0) {
          return filtered[0];
        }
      }
      return null;
    },
    hasAccountNumber () {
      return !!this.accountNumber 
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
      this.$router.push({name: 'view-account', params: {accountid: this.accountId}});
    },
    openNewAliasModal() {
      this.newAliasModalActive = true;
    },
    aliasNameChkBoxChange(newValue) {
      if (!newValue) {
        this.modalAliasAccountName = null;
      }
    },
    aliasNumberChkBoxChange(newValue) {
      if (!newValue && !this.hasAccountNumber) {
        this.modalAliasAccountNumber = null;
      }
    },
    closeModal() {
      this.newAliasModalActive = false;
    },
    async addAlias() {
      if (this.checkModalAliasExists()) {
        this.popNewAliasFailureToast();
      }
      await this.account.newAlias({name: this.modalAliasAccountName, number: this.modalAliasAccountNumber});
      await this.refreshAccount();
      this.newAliasModalActive = false;
    },
    popNewAliasFailureToast() {
      this.$buefy.toast.open({
        message: this.$t('account.alias_already_exists'),
        type: 'is-danger'
      })
    },
    checkModalAliasExists() {
      let all = [{name: this.account.name, number: this.account.number}, ...this.account.aliases];
      return all.filter(a => a.name == this.modalAliasAccountName && a.number == this.modalAliasAccountNumber).length > 0;
    },
    async refreshAccount() {
      this.account = await this.fetchAccount();
    }
  }
})
</script>

<style lang="scss" scoped>
section {
  margin-bottom: 10px;
} 
</style>