<template>
  <div>
    <section class="level title-section">
      <div class="level-left">
        <h3 class="title" v-if="!accountGroupId">{{$t('account_group.creation')}}</h3>
        <h3 class="title" v-if="accountGroupId">{{$t('account_group.update')}}</h3>
      </div>
      <div class="level-left">
        <b-button v-on:click="send" class="level-item is-small" icon-right="plus">{{$t('save')}}</b-button>
      </div>
    </section>
    <section class="submit-section">
      <b-field :label="$t('name')" label-position="on-border">
        <b-input v-model="accountGroup.name" ></b-input>
      </b-field>
      <b-field :label="$t('description')" label-position="on-border">
        <b-input v-model="accountGroup.description" maxlength="200" type="textarea"></b-input>
      </b-field>
      <div class="control level">
        <account-drop-down-selector
          class="level-item"
          :accounts="candidateAccounts"
          v-model="selectedAccountInDrowdown" >
        </account-drop-down-selector>
        <b-field label-position="on-border" class="level-item" narrowed>
          <b-button icon-right="plus" @click="selectAccount" class="addButton"></b-button>
        </b-field>
      </div>
      <div class="control">
        <b-table
          :data="accountGroup.accounts"
          :title="$t('selection')">

          <b-table-column field="name" :label="$t('account.name')" v-slot="props" sortable>
            <string-or-null-display :value="props.row.name" ></string-or-null-display>
          </b-table-column>
          
          <b-table-column field="number" :label="$t('account.number')" v-slot="props" sortable>
            <string-or-null-display :value="props.row.number" ></string-or-null-display>
          </b-table-column>

          <b-table-column field="balance" :label="$t('account.balance')" v-slot="props" sortable>
            <currency-display :currency="props.row.currency" :amount="props.row.balance" :color="false"></currency-display>
          </b-table-column>

          <b-table-column :label="$t('explore')" v-slot="props">
            <b-field>
              <b-button class="table-button is-small is-primary" icon-right="eye" @click="() => goToAccount(props.row.id)"></b-button>
              <b-button class="table-button is-small is-danger" icon-right="times" @click="() => unselectAccount(props.row.id)"></b-button>
            </b-field>
          </b-table-column>

        </b-table>
      </div>
    </section>

  </div>
</template>

<script>
import Vue from 'vue';
import { defineComponent } from '@vue/composition-api';
import AccountGroup from '@/utils/api/AccountGroup';
import Account from '@/utils/api/Account';
import AccountTable from '@/components/accounts/AccountTable';
import AccountDropDownSelector from '@/components/accounts/AccountDropDownSelector';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import {getColumns, queryFilter} from '../components/accounts/AccountTableData.js';

export default defineComponent({
  components: { AccountTable, AccountDropDownSelector, StringOrNullDisplay, CurrencyDisplay },
  data() {
    return {
      accountGroup: new AccountGroup(),
      tableColumns: getColumns(this),
      selectedAccountInDrowdown: null,
      queryFilter,
      accounts: []
    }
  },
  async created() {
    if (this.hasAccountGroupId) {
      this.accountGroup = await this.getAccountGroup();
    }
    this.accounts = await this.getAllAccounts();
    Vue.set(this.accountGroup, 'accounts', this.accountGroup.accounts);
  },
  computed: {
    accountGroupId() {
      return this.$route.params.groupid;
    },
    hasAccountGroupId() {
      return !!this.accountGroupId;
    },
    candidateAccounts() {
      if (this.accounts.length == 0) {
        return [];
      } else {
        if (this.accountGroup.accounts && this.accountGroup.accounts.length > 0) {
          let selectedSet = new Set(this.accountGroup.accounts.map(a => a.id));
          return this.accounts.filter(a => !selectedSet.has(a.id));
        } else {
          return this.accounts;
        }
      }
    }
  },
  methods: {
    async getAllAccounts() {
      return await Account.fetchAll();
    },
    selectAccount() {
      if (this.selectedAccountInDrowdown) {
        this.accountGroup.accounts.push(this.selectedAccountInDrowdown);
        this.selectedAccountInDrowdown = null;
      }
    },
    unselectAccount(accountId) {
      this.accountGroup.accounts = this.accountGroup.accounts.filter(a => a.id != accountId); 
    },
    goToAccount() {
      this.$router.push({ name: 'view-account' })
    },
    async send() {
      this.accountGroup.save().then(() => {
        this.$router.go(-1);
      });
    },
    async getAccountGroup() {
      if (this.hasAccountGroupId) {
        return await new AccountGroup({id: this.accountGroupId}).fetch();
      } else {
        return null;
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.title {
  margin: 10px;
}

.addButton {
  margin-bottom: 10px;
}

.table-button {
  margin-right: 5px;
}
</style>