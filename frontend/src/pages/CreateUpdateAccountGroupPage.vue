<template>
  <div>
    <section class="level title-section">
      <div class="level-left">
        <h3 class="title" v-if="!groupId">{{$t('account_group.creation')}}</h3>
        <h3 class="title" v-if="groupId">{{$t('account_group.update')}}</h3>
      </div>
      <div class="level-left">
        <b-button v-on:click="send" class="level-item is-small" icon-right="save" type="is-info">{{$t('save')}}</b-button>
      </div>
    </section>

    <section class="base-data-section">
      <b-field :label="$t('name')" label-position="on-border">
        <b-input v-model="group.name" ></b-input>
      </b-field>

      <b-field :label="$t('description')" label-position="on-border">
        <b-input v-model="group.description" maxlength="200" type="textarea"></b-input>
      </b-field>
    </section>

    <section class="level title-section">
      <div class="level-left">
        <h2 class="subtitle">{{$t('account.accounts')}}</h2>
      </div>
      <div class="level-left">
        <b-button v-on:click="selectAccount" class="level-item is-small" icon-right="plus">{{$t('account_group.edit.add_account')}}</b-button>
      </div>
    </section>

    <section class="account-section">
      <b-message  type="is-info" class="is-small"><b-icon icon="info-circle"/>{{$t('account_group.edit.info-accounts')}}</b-message>
      <account-drop-down-selector
        :label="$t('account.name')" class="level-item"
        :accounts="candidateAccounts"
        v-model="selectedAccountInDrowdown" expanded>
      </account-drop-down-selector>
      <b-field :label="$t('account_group.contribution_ratio')" label-position="on-border">
        <b-input v-model="selectedContributionRatio" type="number" min="0.000001" step="0.000001" max="1"  placeholder="1" />
      </b-field>
      
      <div class="control">
        <b-table
          :data="group.account_groups"
          :title="$t('selection')">

          <b-table-column field="name" :label="$t('account.name')" v-slot="props" sortable>
            <string-or-null-display :value="props.row.account.name" ></string-or-null-display>
          </b-table-column>
          
          <b-table-column field="number" :label="$t('account.number')" v-slot="props" sortable>
            <string-or-null-display :value="props.row.account.number" ></string-or-null-display>
          </b-table-column>
          
          <b-table-column field="number" :label="$t('account_group.contribution_ratio')" v-slot="props" sortable>
            <span v-if="props.row.contribution_ratio">{{100 * props.row.contribution_ratio}} %</span>
            <span v-else class="tag">{{$t('undefined')}}</span>
          </b-table-column>

          <b-table-column field="balance" :label="$t('account.balance')" v-slot="props" sortable>
            <currency-display :currency="props.row.account.currency" :amount="props.row.account.balance" :color="false"></currency-display>
          </b-table-column>

          <b-table-column :label="$t('explore')" v-slot="props">
            <b-field>
              <b-button class="table-button is-small is-primary" icon-right="eye" @click="() => goToAccount(props.row.id_account)"></b-button>
              <b-button class="table-button is-small is-danger" icon-right="times" @click="() => unselectAccount(props.row.id_account)"></b-button>
            </b-field>
          </b-table-column>

        </b-table>
      </div>
    </section>

  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Group from '@/utils/api/Group';
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
      group: new Group(),
      tableColumns: getColumns(this),
      selectedAccountInDrowdown: null,
      selectedContributionRatio: 1,
      queryFilter,
      accounts: [],
      accountGroups: [],
    }
  },
  async created() {
    if (this.hasGroupId) {
      this.group = await this.getGroup();
    }
    this.accounts = await this.getAllAccounts();
  },
  computed: {
    groupId() {
      return this.$route.params.groupid;
    },
    hasGroupId() {
      return !!this.groupId;
    },
    candidateAccounts() {
      if (this.accounts.length == 0) {
        return [];
      } else {
        if (this.group.account_groups && this.group.account_groups.length > 0) {
          let selectedSet = new Set(this.group.account_groups.map(a => a.id));
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
      if (this.selectedAccountInDrowdown && this.selectedContributionRatio) {
        let accountGroup = {
          "account": this.selectedAccountInDrowdown,
          "id_group": this.group.id,
          "id_account": this.selectedAccountInDrowdown.id,
          "contribution_ratio": this.selectedContributionRatio 
        };
        this.group.account_groups.push(accountGroup);
        this.selectedAccountInDrowdown = null;
        this.selectedContributionRatio = 1;
      }
    },
    unselectAccount(accountId) {
      this.group.account_groups = this.group.account_groups.filter(a => a.id_account != accountId); 
    },
    goToAccount() {
      this.$router.push({ name: 'view-account' })
    },
    async send() {
      this.group.save().then(() => {
        this.$router.go(-1);
      });
    },
    async getGroup() {
      if (this.hasGroupId) {
        return await new Group({id: this.groupId}).fetch();
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