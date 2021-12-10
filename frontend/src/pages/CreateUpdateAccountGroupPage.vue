<template>
  <div>
    <h3 class="title" v-if="!accountGroupId">{{$t('account_group.creation')}}</h3>
    <h3 class="title" v-if="accountGroupId">{{$t('account_group.update')}}</h3>

    <section>
      <div class="control">
        <b-field :label="$t('name')" label-position="on-border">
          <b-input v-model="accountGroup.name" ></b-input>
        </b-field>
      </div>
      <div class="control">
        <b-field :label="$t('description')" label-position="on-border">
          <b-input v-model="accountGroup.description" maxlength="200" type="textarea"></b-input>
        </b-field>
      </div>
    </section>
    <section>
      <double-table-select
        :data="accounts"
        :columns="tableColumns"
        :notSelected="notSelectedAccounts"
        :selected.sync="accountGroup.accounts"
        :filterFromQuery="queryFilter"
        :keyFn="(e) => e.id"
        ></double-table-select>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import AccountGroup from '@/utils/api/AccountGroup';
import Account from '@/utils/api/Account';
import DoubleTableSelect from '@/components/generic/DoubleTableSelect.vue';
import {getColumns, queryFilter} from '../components/accounts/AccountTableData.js';

export default defineComponent({
  components: { DoubleTableSelect },
  data() {
    return {
      accountGroup: new AccountGroup(),
      tableColumns: getColumns(this),
      queryFilter,
      accounts: [],
      notSelectedAccounts: []
    }
  },
  async created() {
    if (this.accountGroupId) {
      this.accountGroup = this.accountGroup.fetch(this.accountGroupId);
    }
    await this.getAllAccounts();
  },
  computed: {
    accountGroupId() {
      return this.$route.params.groupid;
    },
  },
  methods: {
    async getAllAccounts() {
      this.accounts = await Account.fetchAll();
      if (this.accountGroup.accounts) {
        let selectedIdSet = new Set(this.accountGroup.accounts.map(a => a.id))
        this.notSelectedAccounts = this.accounts.filter(a => !selectedIdSet.has(a.id));
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.control {
  margin-top: 10px;
}

.title {
  margin: 10px;
}
</style>