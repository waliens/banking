<template>
    <div>
      <h1 class="title">Group <em>{{group.name}}</em></h1>
      <section class="level">
        <div class="level-item has-text-centered">
          <div>
            <p class="heading">{{$t('account_group.number_accounts')}}</p>
            <p class="title">{{group.accounts.length}}</p>
          </div>
        </div>
        <div class="level-item has-text-centered">
          <div>
            <p class="heading">{{$t('balance')}}</p>
            <p class="title"><currency-display :currency="currency" :amount="overallBalance" :do-color="true"></currency-display></p>
          </div>
        </div>
      </section>
      <section>
        <account-table :accounts="group.accounts"></account-table>
      </section>
    </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountTable from '../components/accounts/AccountTable.vue';
import currency from 'currency.js';
import CurrencyDisplay from '../components/generic/CurrencyDisplay.vue';

export default defineComponent({
  components: {AccountTable, CurrencyDisplay},
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    overallBalance() {
      let balance = currency(0);
      return this.group.accounts.map(a => currency(a.balance)).reduce((o, b) => o.add(b), balance);
    },
    currency() {
      // if all accounts currencies are the same, pick this one. Otherwise, do not display it (TODO make something smarter)
      let currencies = this.group.accounts.map(a => a.currency);
      let defaultCurrency = currencies[0];
      let matches = currencies.slice(1).filter(c => c.id == defaultCurrency.id);
      if (matches.length != currencies.length - 1) {
        return "";
      } else {
        return defaultCurrency;
      }
    }
  }
})
</script>

<style lang="scss">

</style>