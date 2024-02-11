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
          <p class="title">{{group.account_groups.length}}</p>
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
      <b-tabs v-model="activeTab">
        <b-tab-item :label="$t('account.accounts')">
          <account-group-table :account-groups="group.account_groups"></account-group-table>
        </b-tab-item>
        <b-tab-item :label="$t('stats.tabs.inout')">
          <income-expense-chart :group="group" :visible="activeTab==1"></income-expense-chart>
        </b-tab-item>
        <b-tab-item :label="$t('stats.tabs.category')">
          <per-category-chart :group="group" :visible="activeTab==2"></per-category-chart>
        </b-tab-item>
        <b-tab-item :label="$t('stats.tabs.category_monthly')">
          <per-category-monthly-chart :group="group" :visible="activeTab==3"></per-category-monthly-chart>
        </b-tab-item>
        <b-tab-item>
          <tabular-summary :group="group" :visible="activeTab==4"></tabular-summary>
        </b-tab-item>
      </b-tabs>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountGroupTable from '@/components/accounts/AccountGroupTable.vue';
import currency from 'currency.js';
import { strcurrency } from '@/utils/helpers';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay.vue';
import IncomeExpenseChart from '@/components/statistics/IncomeExpenseChart.vue';
import PerCategoryChart from '@/components/statistics/PerCategoryChart.vue';
import PerCategoryMonthlyChart from '@/components/statistics/PerCategoryMonthlyChart.vue';

export default defineComponent({
  components: {
    AccountGroupTable, CurrencyDisplay, IncomeExpenseChart, PerCategoryChart, PerCategoryMonthlyChart
  },
  data() {
    return {
      activeTab: 0
    }
  },
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    overallBalance() {
      let balance = currency(0);
      return this.group.account_groups.map(ag => strcurrency(ag.account.balance)).reduce((o, b) => o.add(b), balance);
    },
    currency() {
      // if all accounts currencies are the same, pick this one. Otherwise, do not display it (TODO make something smarter)
      let currencies = this.group.account_groups.map(ag => ag.account.currency);
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
