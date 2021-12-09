<template>
  <div>
    <!-- Existing groups -->
    <section v-if="groups && groups.length > 0">
      <div class="field is-grouped">
        <div class="control">
          <b-field :label="$t('account_group.tag')">
            <b-select v-model="selectedGroup" :placeholder="$t('account_group.select_one')">
              <option
                v-for="grp in groups"
                :value="grp"
                :key="grp.id">
                {{ grp.name }}
              </option>
            </b-select>
            <div class="control">
              <button class="button is-link">{{$t('new')}}</button>
            </div>
          </b-field>
        </div>
      </div>
    </section>

    <!-- No Data : must create a group or upload transactions -->
    <section v-else>
      <b-message 
        type="is-info" has-icon>
        {{$t('account_group.no_account_group_message')}}
      </b-message>
      <div class="field is-grouped">
        <div class="control">
          <button v-on:click="gotoCreateGroup" class="button is-link">{{$t('account_group.create_account_group')}}</button>
        </div>
        <div class="control">
          <button v-on:click="goToUpload" class="button is-link is-light">{{$t('transaction.upload_data')}}</button>
        </div>
      </div>
    </section>

    <!-- Group selected display accounts -->
    <section v-if="selectedGroup">
      <account-table :accounts="selectedGroup.accounts"></account-table>
      <div class="control">
        <button class="button is-link">{{$t('select')}}</button>
      </div>
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
      groups: null,
      selectedGroup: null
    }
  },

  async created() {
    await this.fetchGroups()
  },

  methods: {
    async fetchGroups() {
      await AccountGroup.fetchGroups().then(groups => { this.groups = groups; });
    },
    selectGroup() {
      // TODO
    },
    goToUpload() {
      this.$router.push({ name: 'upload_data' });
    },
    gotoCreateGroup() {
      this.$route.push({ name: 'update_account_group' });
    }
  }
})
</script>

<style lang="scss" scoped>

</style>