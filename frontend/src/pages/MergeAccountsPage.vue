<template>
  <div>
    <section class="level">
      <div class="level-left"><h3 class="level-item title">{{$t('account.merge')}}</h3></div>
      <div class="level-right">
        <div class="level-left"> <b-button v-on:click="mergeWarning" class="level-item is-small" icon-right="cog">{{$t('merge')}}</b-button></div>
      </div>
    </section>
    <section class="level">
      <div class="level-left">
        <p class="level-item">{{$t('string.matching.auto-match')}}</p>
        <b-field class="match-field-level level-item" :label="$t('string.matching.strategy')" label-position="on-border">
          <b-select placeholder="Select a name" v-model="matchStrategy" size="is-small" :disabled="!selectedRepr" expanded>
            <option
                v-for="strategy in matchStrategies"
                :value="strategy"
                :key="strategy">
                {{strategy}}
            </option>
          </b-select>
        </b-field>
        <b-field class="match-field-level level-item">
          <b-button icon-right="chevron-left" size="is-small" :disabled="!selectedRepr || matchingCurrentIndex <= 0" @click="prevMatch"></b-button>
        </b-field>
        <b-field class="match-field-level level-item">
          <b-button icon-right="chevron-right" size="is-small" :disabled="!selectedRepr || matchingCurrentIndex >= matchCandidates.length - 1" @click="nextMatch"></b-button>
        </b-field>
        <p>{{$t('string.matching.matches')}}: <em>{{matchingCurrentIndex+1}} / {{matchCandidates.length}}</em></p>
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
          <account-alias-table 
            :aliases="getAliases(selectedRepr)" 
            :title="$t('account.aliases')">
          </account-alias-table>
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
          <account-alias-table
            :aliases="getAliases(selectedAlias)" 
            :title="$t('account.aliases')">
          </account-alias-table>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountDropDownSelector from '../components/accounts/AccountDropDownSelector.vue'
import Account from '@/utils/api/Account';
import AccountAliasTable from '../components/accounts/AccountAliasTable.vue';
import { getStrategies, matchAndSortArray } from '@/utils/stringmatch';

export default defineComponent({
  components: { AccountDropDownSelector, AccountAliasTable },
  data() {
    return {
      accounts: [],
      selectedRepr: null,
      selectedAlias: null,
      matchStrategies: getStrategies(),
      matchStrategy: getStrategies()[0],
      matchingCurrentIndex: -1,
      matchCandidates: []
    };
  },
  async created() {
    this.accounts = await this.fetchAccounts(); 
  },
  methods: {
    async fetchAccounts() {
      return await Account.fetchAll();
    },
    getAliases(account) {
      if (!account) {
        return [];
      }
      return account.aliases;
    },
    mergeWarning() {
      if (!this.selectedRepr || !this.selectedAlias) {
        this.$buefy.toast.open({
            message: this.$t("account.no_account_selected"),
            type: 'is-danger',
            hasIcon: true
        })
      }
      this.$buefy.dialog.confirm({
        title: this.$t('account.merge_warning.title'),
        message: this.$t('account.merge_warning.text', {
          'alias': this.selectedAlias.formatName(this), 
          'reference': this.selectedRepr.formatName(this)
        }),
        cancelText: this.$t('cancel'),
        confirmText: this.$t('confirm'),
        type: 'is-warning',
        hasIcon: true,
        onConfirm: this.merge
      });
    },
    async merge() {
      if (!this.selectedRepr || !this.selectedAlias) {
        return;
      }
      await Account.merge(this.selectedRepr.id, this.selectedAlias.id).then(() => {
        this.$router.go();
      }).catch(e => {
        this.$buefy.toast.open({
            message: e.response.data.msg,
            type: 'is-error'
        })
      })
    },
    swapSelected() {
      let tmp = this.selectedRepr;
      this.selectedRepr = this.selectedAlias;
      this.selectedAlias = tmp;
    },
    getMatchCandidates() {
      if (!this.selectedRepr || !this.selectedRepr.name) {
        return [];
      }
      let sorted = matchAndSortArray(
        this.matchStrategy, 
        this.selectedRepr,
        this.accounts.filter(account => account.id != this.selectedRepr.id && account.name), 
        o => o.name  
      );
      return sorted;
    },
    nextMatch() {
      this.matchingCurrentIndex++;
      this.selectedAlias = this.matchCandidates[this.matchingCurrentIndex].obj;
    },
    prevMatch() {
      this.matchingCurrentIndex--;
      this.selectedAlias = this.matchCandidates[this.matchingCurrentIndex].obj;
    }
  },
  computed: {
   
  },
  watch: {
    matchStrategy: function(newStrategy, oldStrategy) {
      if (newStrategy != oldStrategy) {
        this.matchingCurrentIndex = -1;
        this.selectedAlias = null;
        this.matchCandidates = this.getMatchCandidates();
      }
    },
    selectedRepr: function(newRepr, oldRepr) {
      if (newRepr != oldRepr || (newRepr && oldRepr && newRepr.id != oldRepr.id)) {
        this.matchingCurrentIndex = -1;
        if (newRepr) {
          this.matchCandidates = this.getMatchCandidates();
        }
      } 
    }
  }
})
</script>

<style lang="scss" scoped>
.match-field-level {
  margin-bottom: 5px;
  margin-left: 5px;
}
</style>