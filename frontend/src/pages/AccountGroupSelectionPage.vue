<template>
  <div>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('account_group.selection')}}</h3></div>
      <div class="level-right">
        <b-button v-if="selectedAccountGroup" class="level-item is-small is-secondary" @click="editGroup" icon-right="pen">{{$t('edit')}}</b-button>
        <b-button v-if="selectedAccountGroup" class="level-item is-small is-secondary" @click="selectGroup" icon-right="hand-pointer">{{$t('select')}}</b-button>
        <b-button @click="createGroup" class="level-item is-small" icon-right="plus">{{$t('account_group.create_account_group')}}</b-button>
      </div>
    </section>
    
    <!-- Existing groups -->
    <section v-if="accountGroups && accountGroups.length > 0">
      <div class="field is-grouped">
        <div class="control">
          <b-field :label="$t('account_group.tag')" label-position="on-border">
            <b-select v-model="selectedAccountGroup" :placeholder="$t('account_group.select_one')">
              <option
                v-for="grp in accountGroups"
                :value="grp"
                :key="grp.id">
                {{ grp.name }}
              </option>
            </b-select>
          </b-field>
        </div>
      </div>

      <!-- Group selected display accounts -->
      <div v-if="selectedAccountGroup">
        <account-table :accounts="selectedAccountGroup.accounts" :title="$t('account.accounts')"></account-table>
      </div>
    </section>

    <!-- No Data : must create a group or upload transactions -->
    <section v-else>
      <b-message 
        type="is-info" has-icon>
        {{$t('account_group.no_account_group_message')}}
      </b-message>
    </section>

  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import AccountGroup from '@/utils/api/AccountGroup';
import AccountTable from '../components/accounts/AccountTable.vue';

export default defineComponent({
  components: {AccountTable},

  data() {
    return {
      accountGroups: null,
      selectedAccountGroup: null
    }
  },
  async created() {
    await this.fetchAccountGroups()
  },
  methods: {
    async fetchAccountGroups() {
      await AccountGroup.fetchGroups().then(groups => { this.accountGroups = groups; });
    },
    selectGroup() {
      if (this.selectedAccountGroup) {
        this.$store.dispatch('setCurrentGroup', new AccountGroup(this.selectedAccountGroup));
        this.$router.push({ name: 'home' });
      }
    },
    createGroup() {
      this.$router.push({ name: 'create-account-group' });
    },
    editGroup() {
      this.$router.push({ name: 'edit-account-group', params: { groupid: this.selectedAccountGroup.id }});
    }
  }
})
</script>

<style lang="scss" scoped>

</style>