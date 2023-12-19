<template>
  <div>
    <b-field :label="$t('amount')" class="amountRangeField">
      <amount-range-log-slider v-model="amountRange" expanded></amount-range-log-slider>
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
      <account-drop-down-selector :label="$t('transaction.filters.accountFrom')" v-model="accountFrom" :accounts="accounts_" expanded></account-drop-down-selector>
      <account-drop-down-selector :label="$t('transaction.filters.accountTo')"  v-model="accountTo" :accounts="accounts_" expanded></account-drop-down-selector>
    </b-field>
    <b-field :label="$t('transaction.filters.category')" label-position="on-border" expanded>
      <b-field grouped>
        <b-select v-model="categoryId" @input="categoryUpdated" expanded>
          <option v-for="breadcrumb in breadcrumbs" :key="breadcrumb.id" :value="breadcrumb.id">
            {{breadcrumb.breadcrumb}}
          </option>
          <p class="control">
            <b-button icon-right="multiply" @click="categoryId = null"></b-button>
          </p>
        </b-select>
        <b-field>
          <b-switch v-model="includeLabeled" @input="includeLabeledUpdated">
            {{ $t('transaction.filters.include_labeled') }}
          </b-switch>
        </b-field>
      </b-field>

    </b-field>
    <b-field grouped>
      <b-field label-position="on-border">
        <template #label>
          <b-tooltip :label="$t('transaction.filters.in_group_tooltip')">{{$t('transaction.filters.in_group')}}</b-tooltip>
        </template>
        <b-select v-model="keepCurrentGroup">
          <option v-for="option in inCurrentGroupOptions" :key="option" :value="option">
            {{ $t(`transaction.filters.in_group_options.${option}`) }}
          </option> 
        </b-select>
      </b-field>
      <b-field>
        <b-tooltip :label="$t('transaction.filters.include_intra_profile_tooltip')">
          <b-switch v-model="includeIntraProfile">
            {{ $t('transaction.filters.include_intra_profile') }}
          </b-switch>
        </b-tooltip>
      </b-field>

    </b-field>

    <b-field class="level">
      <div class="level-right">
        <b-button class="level-item is-small is-primary" @click="clickClear" icon-right="times">{{$t('clear')}}</b-button>
        <b-button class="level-item is-small is-primary" @click="clickFilter" icon-right="filter">{{$t('filter')}}</b-button>
      </div>
    </b-field>
  </div>
</template>

<script>
import moment from 'moment';
import Account from '@/utils/api/Account';
import Category from '@/utils/api/Category';
import AccountDropDownSelector from '@/components/accounts/AccountDropDownSelector';
import AmountRangeLogSlider from '@/components/generic/AmountRangeLogSlider';
import { defineComponent } from '@vue/composition-api';


export default defineComponent({
  components: {AccountDropDownSelector, AmountRangeLogSlider},
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
      includeLabeled: false,
      includeIntraProfile: false,
      keepCurrentGroup: "only_in_group",
      amountRange: [0, 999999],
      periodFrom: null,
      periodTo: null,
      accountFrom:  null,
      accountTo:  null,
      categoryId: null,
      periodFromSelected: false,
      periodToSelected: false,
      categories_: [],
      accounts_: [],
      inCurrentGroupOptions: [
        "only_in_group",
        "only_out_group",
        "both_in_out_group"
      ]
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
      this.includeLabeled = false;
      this.amountRange = [0, 999999];
      this.includeIntraProfile = false;
      this.inCurrentGroupOptions = "only_in_group";
      this.clearFn();
    },
    clickFilter() {
      let filters = {
        periodFrom: this.periodFrom,
        periodTo: this.periodTo,
        accountFrom: this.accountFrom,
        accountTo: this.accountTo, 
        category: this.categoryId,
        amountFrom: this.amountRange[0],
        amountTo: this.amountRange[1],
        includeIntraProfile: this.includeIntraProfile,
        includeLabeled: this.includeLabeled,
        keepCurrentGroup: this.keepCurrentGroup
      };
      this.filterFn(filters);
    },
    categoryUpdated(newValue, oldValue) {
      if (newValue != oldValue && newValue) {
        this.includeLabeled = true;
      }
    },
    includeLabeledUpdated(newValue, oldValue) {
      if (newValue != oldValue) {
        this.categoryId = null;        
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.amountRangeField {
  margin-left: 10px;
  margin-right: 10px;
}
</style>