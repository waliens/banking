<template>
  <div>
    <b-field>
      <b-switch v-model="filtersEnabled">
        {{ $t('transaction.filters.enabled') }}
      </b-switch>
    </b-field>
    <b-field grouped>
      <b-field :label="$t('transaction.filters.periodFrom')" label-position="on-border" expanded>
        <b-datepicker
          v-model="periodFromDate"
          :show-week-number="true"
          icon="calendar-today"
          :icon-right="periodFromSelected ? 'times-circle' : ''"
          icon-right-clickable
          @icon-right-click="clearDate"
          trap-focus>
        </b-datepicker>
      </b-field>
      <b-field :label="$t('transaction.filters.periodTo')" label-position="on-border" expanded>
        <b-datepicker
          v-model="periodToDate"
          :show-week-number="true"
          icon="calendar-today"
          :icon-right="periodToSelected ? 'times-circle' : ''"
          icon-right-clickable
          @icon-right-click="clearDate"
          trap-focus>
        </b-datepicker>
      </b-field>
    </b-field>
    <b-field grouped>
      <b-field :label="$t('transaction.filters.accountFrom')" label-position="on-border" expanded>
        <account-drop-down-selector v-model="accountFrom" :accounts="accounts_"></account-drop-down-selector>
      </b-field>
      <b-field :label="$t('transaction.filters.accountTo')" label-position="on-border" expanded>
        <account-drop-down-selector v-model="accountTo" :accounts="accounts_"></account-drop-down-selector>
      </b-field>
    </b-field>
    <b-field :label="$t('transaction.filters.category')" label-position="on-border" expanded>
      <b-select v-model="categoryId" expanded>
        <option v-for="breadcrumb in breadcrumbs" :key="breadcrumb.id" :value="breadcrumb.id">
          {{breadcrumb.breadcrumb}}
        </option>
      </b-select>
    </b-field>
  </div>
</template>

<script>
import moment from 'moment';
import Account from '@/utils/api/Account';
import Category from '@/utils/api/Category';
import AccountDropDownSelector from '@/components/accounts/AccountDropDownSelector';
import { defineComponent } from '@vue/composition-api';


export default defineComponent({
  components: {AccountDropDownSelector},
  name: "TransactionsFilterForm",
  props: {
    periodFrom: { type: moment, default: () => moment().subtract('1 month') },
    periodTo: { type: moment, default: () => moment() },
    accountFrom: { type: Account, default: () => null },
    accountTo: { type: Account, default: () => null },
    categoryId: { type: Number, default: () => null },
    accounts: { type: Array, default: () => [] },
    categories: { type: Array, default: () => [] }
  },
  data() {
    return {
      // filters
      filtersEnabled: false,
      periodFromSelected: false,
      periodToSelected: false,
      categories_: [],
      accounts_: [] 
    }
  },
  async created() {
    // download only if not passed by parent
    if (this.categories.length == 0) {
      this.categories_ = await Category.getCategoryTree();
    } else {
      this.categories_ = this.categories;
    }

    if (this.accounts.length == 0) { 
      this.accounts_ = await Account.fetchAll();
    } else {
      this.accounts_ = this.accounts;
    }
  },
  computed: {
    breadcrumbs() {
      return Category.getStringBreadcrumbs(this.categories_);
    },
    periodFromDate: {
      get() {
        return this.periodFrom ? this.periodFrom.toDate() : null;
      },
      set(value) {
        this.periodFrom = value ? moment(value) : null;
      }
    },
    periodToDate: {
      get() {
        return this.periodTo ? this.periodTo.toDate() : null;
      },
      set(value) {
        this.periodTo = value ? moment(value) : null;
      }
    }
  },
  methods: {
    clearDate(isFrom) {
      if (isFrom) {
        this.periodFromDate = null;
      } else {
        this.periodToDate = null;
      }
    }
  }
})
</script>
