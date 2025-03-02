<template>
  <div v-if="account">
    <section class="level">
      <div class="level-right"><h3 class="level-item title">{{$t('account.details')}}</h3></div>
      <div class="level-left"> <b-button v-on:click="goToEditEvent" class="level-item is-small" icon-right="pen">{{$t('edit')}}</b-button></div>
    </section>

    <section class="level">
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">{{$t('account.number')}}</p>
          <p ><account-number-display :number="account.number"></account-number-display></p>
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">{{$t('account.name')}}</p>
          <p >{{account.name}}</p>
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">{{$t('balance')}}</p>
          <p ><currency-display :currency="account.currency" :amount="account.balance" :do-color="true"></currency-display></p>
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">{{$t('account.initial')}}</p>
          <p><currency-display :currency="account.currency" :amount="account.initial" :do-color="true"></currency-display></p>
        </div>
      </div>
    </section>

    <section class="alias-list">
      <span>{{$t("account.aliases")}}:</span> <span v-for="alias in account.aliases" v-bind:key="alias.id" class="tag is-primary alias-tag">{{formatAlias(alias)}}</span>
    </section>

    <section v-if="transactions && account">
      <transaction-table
        :transactions="transactions"
        :reference-account="account"
        :title="$t('transaction.transactions')"
        @load-more-transactions="loadMoreTransactions"
      ></transaction-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Account from '@/utils/api/Account';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay.vue';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay.vue';
import TransactionTable from '@/components/transactions/TransactionTable.vue';

export default defineComponent({
  components: {CurrencyDisplay, TransactionTable, AccountNumberDisplay},
  data() {
    return {
      account: null,
      transactions: [],
      start: 0,
      count: 50
    };
  },
  async created() {
    if (this.hasAccountId) {
      this.account = await this.fetchAccount();
      this.transactions = await this.fetchTransactions();
    }
  },
  computed: {
    hasAccountId() {
      return !!this.accountId;
    },
    accountId() {
      return this.$route.params.accountid;
    }
  },
  methods: {
    async fetchAccount() {
      return await new Account({id: this.accountId}).fetch();
    },
    async fetchTransactions() {
      if (this.account) {
        let result = await this.account.transactions({start: this.start, count: this.count});
        this.start += this.count;
        return result;
      } else {
        return [];
      }
    },
    async loadMoreTransactions() {
      let moreTransactions = await this.fetchTransactions();
      this.transactions = [...this.transactions, ...moreTransactions];
    },
    formatAlias(alias) {
      return Account.formatNameByObj(alias, this);
    },
    goToEditEvent() {
      this.$router.push({'name': 'edit-account', params: {accountid: this.accountId}});
    }
  }
})
</script>

<style lang="scss" scoped>
.alias-list {
  margin-bottom: 10px;
}

.edit-initial {
  margin-left: 5px;
}

.alias-tag {
  margin-right: 5px;
}
</style>