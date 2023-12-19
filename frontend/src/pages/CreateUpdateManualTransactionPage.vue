<template>
  <div v-if="transaction">
    <section class="level title-section">
      <div class="level-left">
        <h3 class="title" v-if="hasTransactionId">{{$t('transaction.update')}}</h3>
        <h3 class="title" v-else>{{$t('transaction.create')}}</h3>
      </div>
      <div class="level-left">
        <b-button v-on:click="save" class="level-item is-small" icon-right="save" type="is-info">{{$t('save')}}</b-button>
      </div>
    </section>

    <section class="base-data-section">
      <!--  id_source = request.json.get("id_source", type=int, default=None)
          id_dest = request.json.get("id_dest", type=int, default=None)
          id_group = request.json.get("id_group", type=int, default=None)
      -->
      
      <b-field v-if="!hasTransactionId">
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
      addInGroup: true,
      selectedDate: null
    }
  },
  async created() {
    this.loading = true;
    this.transaction = await this.getTransaction();
    this.categories = await Category.getFlattenedCategoryTree();
    this.currencies = await Currency.fetchAll();
    this.loading = false;
    this.accounts = await Account.fetchAll();
  },
  computed: {
    transactionId() {
      return this.$route.params.transactionid;
    },
    hasTransactionId() {
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
      if (this.hasTransactionId) {
        return await Transaction.fetch(this.transactionId);
      } else {
        return new Transaction();
      }
    },
    async save() {
      await this.transaction.save().then((t) => {
        this.$buefy.toast.open({
          message: this.$t('transaction.success'),
          type: 'is-success'
        });
        if (!this.hasTransactionId) {
          this.$router.push({'name': 'edit-transaction', params: {transactionid: t.id}});
        }
      });
    }
  },
  watch: {
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