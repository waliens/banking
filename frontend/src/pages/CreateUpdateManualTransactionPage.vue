<template>
  <div v-if="transaction">
    <section class="level title-section">
      <div class="level-left">
        <h3 class="title" v-if="isUpdate">{{$t('transaction.update')}}</h3>
        <h3 class="title" v-else>{{$t('transaction.create')}}</h3>
      </div>
      <b-field grouped class="level-left">
        <b-field v-if="isUpdate && hasGroupSelected && !isLinkedToCurrentGroup" class="level-item is-small">
          <b-button class="is-small" icon-right="link" type="is-info" v-on:click="link">{{$t('transaction.link')}}</b-button>
        </b-field>
        <b-field v-if="isUpdate && hasGroupSelected && isLinkedToCurrentGroup" class="level-item is-small">
          <b-button class="is-small" icon-right="unlink" type="is-warning" v-on:click="unlink">{{$t('transaction.unlink')}}</b-button>
        </b-field>
        <b-field class="level-item is-small">
          <b-button class="is-small" icon-right="save" type="is-info" v-on:click="save">{{$t('save')}}</b-button>
        </b-field>
      </b-field>
    </section>

    <section class="base-data-section">
      <b-field v-if="hasGroupSelected && !isUpdate">
        <b-checkbox v-model="addInGroup">{{ $t('transaction.fields.add_in_group') }}</b-checkbox>
      </b-field>
      
      <b-field grouped>
        <b-field :label="$t('transaction.fields.amount')" label-position="on-border" expanded>
          <b-numberinput step="0.01" v-model="transaction.amount" />
        </b-field>
        <b-field>
          <currency-selector v-model="transaction.id_currency" :currencies="currencies"></currency-selector>
        </b-field>
      </b-field>

      <b-field grouped>
        <account-drop-down-selector :label="$t('transaction.account.source')" v-model="transaction.source" :accounts="candidateAccounts" :with-to-account="false" expanded />
        <account-drop-down-selector :label="$t('transaction.account.dest')" v-model="transaction.dest" :accounts="candidateAccounts" :with-to-account="false" expanded />
      </b-field>

      <b-field :label="$t('transaction.fields.when')" label-position="on-border">
        <b-datepicker
          v-model="transaction.when"        
          icon-left="-calendar"
          icon-right="close-circle"
          icon-right-clickable
          @icon-right-click="transaction.when = null"
          trap-focus>
        </b-datepicker>
      </b-field>

      <b-field :label="$t('transaction.fields.category')" label-position="on-border" expanded>
        <category-selector v-model="transaction.id_category" :categories="categories" :expanded="true"/>
      </b-field>
      
      <b-field :label="$t('transaction.fields.communication')" label-position="on-border">
        <b-input maxlength="200" type="textarea" v-model="transaction.metadata_.communication" />
      </b-field>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import CategorySelector from '../components/categories/CategorySelector';
import CurrencySelector from '../components/generic/CurrencySelector';
import AccountDropDownSelector from '../components/accounts/AccountDropDownSelector';
import Transaction from '@/utils/api/Transaction';
import Category from '@/utils/api/Category';
import Currency from '@/utils/api/Currency';
import Account from '@/utils/api/Account';

export default defineComponent({
  components: { CategorySelector, CurrencySelector, AccountDropDownSelector },
  data() {
    return {
      transaction: null,
      categories: [],
      currencies: [],
      accounts: [],
      transactionGroups: new Set(),
      addInGroup: true,
      selectedDate: null
    }
  },
  async created() {
    this.loading = true;
    this.transaction = await this.getTransaction();
    this.categories = await Category.getFlattenedCategoryTree();
    this.currencies = await Currency.fetchAll();
    if (this.transaction.id) {
      await this.updateTransactionGroups();
    }
    this.loading = false;
    this.accounts = await Account.fetchAll();
  },
  computed: {
    hasGroupSelected() {
      return !!this.$store.state.currentGroupId;
    },
    isLinkedToCurrentGroup() {
      return this.transaction.id && this.transactionGroups.has(this.$store.state.currentGroupId);
    },
    transactionId() {
      return this.$route.params.transactionid;
    },
    isUpdate() {
      return !!this.transactionId;
    },
    candidateAccounts() {
      if (this.accounts.length == 0) {
        return [];
      } else if (this.transaction == null || (this.transaction.id_source == null && this.transaction.id_dest == null)) {
        return this.accounts;
      } else {
        let selectedSet = new Set();
        if (this.transaction.id_source) {
          selectedSet.add(this.transaction.id_source);
        }
        if (this.transaction.id_dest) {
          selectedSet.add(this.transaction.id_dest);
        }
        return this.accounts.filter(a => !selectedSet.has(a.id));
      }
    }
  },
  methods: {
    async getTransaction() {
      if (this.isUpdate) {
        return await Transaction.fetch(this.transactionId);
      } else {
        return new Transaction();
      }
    },
    async updateTransactionGroups() {
      this.transactionGroups = await this.transaction.getGroupIds();
    },
    async save() {
      let isCreation = !this.transaction.id; 
      await this.transaction.save().then(async (t) => {
        this.$buefy.toast.open({ message: this.$t('success'), type: 'is-success' });
        if (isCreation && this.hasGroupSelected && this.addInGroup) {
          await this.baseLink().catch(() => {});
        }
        if (isCreation) {
          this.transaction = new Transaction();
        }
        this.$router.push({'name': 'edit-transaction', params: {transactionid: t.id}});
      }).catch(() => {
        this.$buefy.toast.open({ message: this.$t('failure'), type: 'is-danger' });
      });
    },
    async baseLink() {
      if (!this.hasGroupSelected) {
        throw Error("not selected current group");
      }
      return await this.$store.state.currentGroup.linkTransactions([this.transaction.id]);
    },
    async link() {
      await this.baseLink().then(async () => {
        await this.updateTransactionGroups();
      }).catch(() => {
        this.$buefy.toast.open({
          message: this.$t('failure'),
          type: 'is-danger'
        });
      });
    },
    async unlink() {
      if (!this.hasGroupSelected) {
        return;
      }
      await this.$store.state.currentGroup.unlinkTransactions([this.transaction.id]).then(async () => {
        await this.updateTransactionGroups();
      }).catch(() => {
        this.$buefy.toast.open({
          message: this.$t('failure'),
          type: 'is-danger'
        });
      });
    }
  },
  watch: {
    '$route.params.transactionid': async function () {   
      this.loading = true;
      this.transaction = await this.getTransaction();
      if (this.transaction.id) {
        await this.updateTransactionGroups();
      }
      this.loading = false;
    },
    'transaction.dest': function (value) {
      if (value) {
        this.transaction.id_dest = value.id;
      } else {
        this.transaction.id_dest = null;
      }
    },
    'transaction.source': function (value) {
      if (value) {
        this.transaction.id_source = value.id;
      } else {
        this.transaction.id_source = null;
      }
    }
  }
})
</script>

<style lang="scss" scoped>
</style>