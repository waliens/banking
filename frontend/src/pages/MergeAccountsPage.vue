<template>
  <div>
    <section class="level">
      <div class="level-left"><h3 class="level-item title">{{$t('account.merge')}}</h3></div>
      <div class="level-right">
        <div class="level-left"> <b-button v-on:click="merge" class="level-item is-small" icon-right="cog">{{$t('merge')}}</b-button></div>
      </div>
    </section>
    <section>
      <div class="columns">
        <div class="column">
          <account-drop-down-selector 
            v-model="selectedRepr"
            :accounts="accounts" 
            :field-title="$t('account.representative')">
          </account-drop-down-selector>
        </div>
        <div class="column is-narrow">
          <b-button v-on:click="swapSelected" icon-right="exchange-alt"></b-button>
        </div>
        <div class="column">
          <account-drop-down-selector 
            v-model="selectedAlias"
            :accounts="accounts" 
            :field-title="$t('account.alias')">
          </account-drop-down-selector>
        </div> 
      </div>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountDropDownSelector from '../components/accounts/AccountDropDownSelector.vue'
import Account from '@/utils/api/Account';

export default defineComponent({
  components: { AccountDropDownSelector },
  data() {
    return {
      accounts: [],
      selectedRepr: null,
      selectedAlias: null
    };
  },
  async created() {
    this.accounts = await this.fetchAccounts(); 
  },
  methods: {
    async fetchAccounts() {
      return await Account.fetchAll();
    },
    merge() {

    },
    swapSelected() {
      let tmp = this.selectedRepr;
      this.selectedRepr = this.selectedAlias;
      this.selectedAlias = tmp;
    }
  }
})
</script>

<style lang="scss" scoped>

</style>