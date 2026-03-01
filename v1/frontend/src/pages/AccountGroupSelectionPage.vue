<template>
  <div>
    <b-loading :is-full-page="false" :active="loading"/>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('account_group.selection')}}</h3></div>
      <div class="level-right">
        <b-button v-if="selectedGroup" class="level-item is-small is-secondary" @click="editGroup" icon-right="pen">{{$t('edit')}}</b-button>
        <b-button v-if="selectedGroup" class="level-item is-small is-secondary" @click="selectGroup" icon-right="hand-pointer">{{$t('select')}}</b-button>
        <b-button @click="createGroup" class="level-item is-small" icon-right="plus">{{$t('account_group.create_account_group')}}</b-button>
      </div>
    </section>
    
    <!-- Existing groups -->
    <section v-if="accountGroups && accountGroups.length > 0">
      <div class="field is-grouped">
        <div class="control">
          <b-field :label="$t('account_group.tag')" label-position="on-border">
            <b-select v-model="selectedGroup" :placeholder="$t('account_group.select_one')">
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
      <div v-if="selectedGroup">
        <account-group-table :accountGroups="selectedGroup.account_groups" :title="$t('account.accounts')"></account-group-table>
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
import Group from '@/utils/api/Group';
import AccountGroupTable from '../components/accounts/AccountGroupTable.vue';

export default defineComponent({
  components: {AccountGroupTable},

  data() {
    return {
      loading: true,
      accountGroups: null,
      selectedGroup: null
    }
  },
  async created() {
    this.loading = true;
    await this.fetchAccountGroups();
    if (this.groupIsActive) {
      let filtered = this.accountGroups.filter(ag => ag.id == this.activeGroup.id);
      if (filtered.length == 1) {
        this.selectedGroup = filtered[0];
      }
    }
    this.loading = false;
  },
  computed: {
    activeGroup() {
      return this.$store.state.currentGroup;
    },
    groupIsActive() {
      return !!this.activeGroup;
    },
  },
  methods: {
    async fetchAccountGroups() {
      await Group.fetchGroups().then(groups => { this.accountGroups = groups; });
    },
    selectGroup() {
      if (this.selectedGroup) {
        this.$store.dispatch('setCurrentGroup', new Group(this.selectedGroup));
        this.$router.push({ name: 'dashboard' });
      }
    },
    createGroup() {
      this.$router.push({ name: 'create-account-group' });
    },
    editGroup() {
      this.$router.push({ name: 'edit-account-group', params: { groupid: this.selectedGroup.id }});
    }
  }
})
</script>

<style lang="scss" scoped>

</style>