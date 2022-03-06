<template>
  <div>
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
    <b-field class="level">
      <div class="level-left">
      </div>
      <div class="level-right">
        <b-button class="level-item is-small" @click="clickClear" icon-right="times">{{$t('clear')}}</b-button>
        <b-button class="level-item is-small" @click="clickFilter" icon-right="filter">{{$t('filter')}}</b-button>
      </div>
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
    accounts: { type: Array, default: () => [] },
    categories: { type: Array, default: () => [] },
    filterFn: { type: Function, default: () => { () => { return; } }},
    clearFn: { type: Function, default: () => { () => { return; } }}
  },
  data() {
    return {
      // filters
      periodFrom: null,
      periodTo: null,
      accountFrom:  null,
      accountTo:  null,
      categoryId: null,
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
    },
    clickClear() {
      this.clearDate(true);
      this.clearDate(false);
      this.periodFromDate = null;
      this.periodToDate = null;
      this.accountFrom = null;
      this.accountTo = null;
      this.categoryId = null;
      this.clearFn();
    },
    clickFilter() {
      let filters = {
        periodFromDate: this.periodFromDate,
        periodToDate: this.periodToDate,
        accountFrom: this.accountFrom,
        accountTo: this.accountTo, 
      };
      this.filterFn(filters);
    }
  }
})
</script>
