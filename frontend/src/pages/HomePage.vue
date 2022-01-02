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
            <p class="title">{{overallBalance}}</p>
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

export default defineComponent({
  components: {AccountTable},
  setup() {
    console.log(this.$store.currentGroup);
  },
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    overallBalance() {
      let balance = currency(0);
      console.log(this.group);
      return this.group.accounts.map(a => currency(a.balance)).reduce((o, b) => o.add(b), balance);
    }
  }
})
</script>

<style lang="scss">

</style>