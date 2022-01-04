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
          <p >{{account.number}}</p>
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

    <section class="equiv-list">
      <span>{{$t("account.alternatives")}}:</span> <span v-for="equiv in account.equivalences" v-bind:key="equiv.id" class="tag is-primary">{{equiv.number}}, {{equiv.name}}</span>
    </section>

    <section v-if="transactions && account">
      <transaction-table :transactions="transactions" :reference-account="account"></transaction-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Account from '@/utils/api/Account';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay.vue';
import TransactionTable from '@/components/transactions/TransactionTable.vue';

export default defineComponent({
  components: {CurrencyDisplay, TransactionTable},
  data() {
    return {
      account: null,
      transactions: null
    };
  },
  async created() {
    this.account = await this.fetchAccount();
    this.transactions = await this.fetchTransactions();
  },
  computed: {
    accountId() {
      return this.$route.params.accountId;
    }
  },
  methods: {
    async fetchAccount() {
      return await Account.fetch(this.accountId);
    },
    async fetchTransactions() {
      if (this.account) {
        return await this.account.transactions();
      } else {
        return [];
      }
      
    },
    goToEditEvent() {
      this.$router.push({'name': 'edit-account', params: {'accountId': this.accountId}});
    }
  }
})
</script>

<style lang="scss" scoped>
.equiv-list {
  margin-bottom: 10px;
}

.edit-initial {
  margin-left: 5px;
}
</style>