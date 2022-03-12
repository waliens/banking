<template>
  <div>
    <section class="level">
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">{{$t('group')}}</p>
          <p class="title">{{group.name}}</p>
        </div>
      </div>
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
      <b-tabs v-model="activetTab">
        <b-tab-item :label="$t('account.accounts')">
          <account-table :accounts="group.accounts"></account-table>
        </b-tab-item>
        <b-tab-item :label="$t('stats.tabs.inout')">
          <income-expense-chart :group="group" :visible="activetTab==1"></income-expense-chart>
        </b-tab-item>
        <b-tab-item :label="$t('stats.tabs.category')">
          <per-category-chart :group="group" :visible="activetTab==2"></per-category-chart>
        </b-tab-item>
      </b-tabs>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountTable from '../components/accounts/AccountTable.vue';
import currency from 'currency.js';
import { strcurrency } from '@/utils/helpers';
import CurrencyDisplay from '../components/generic/CurrencyDisplay.vue';
import IncomeExpenseChart from '../components/charts/IncomeExpenseChart.vue';
import PerCategoryChart from '../components/charts/PerCategoryChart.vue';

export default defineComponent({
  components: {AccountTable, CurrencyDisplay, IncomeExpenseChart, PerCategoryChart},
  data() {
    return {
      activetTab: 0
    }
  },
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    overallBalance() {
      let balance = currency(0);
      return this.group.accounts.map(a => strcurrency(a.balance)).reduce((o, b) => o.add(b), balance);
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
// .divider {
//   display: block;
//   position: relative;
//   border-top: 0.1rem solid #dbdbdb;
//   height: 0.1rem;
//   margin: 2rem 0;
//   text-align: center;
// }

</style>