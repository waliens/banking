<template>
  <table class="table">
    <thead>
      <tr>
        <th></th>
        <th>{{ $t('transaction.duplicate-table.duplicate') }}</th>
        <th>{{ $t('transaction.duplicate-table.original') }}</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>{{ $t('transaction.data_source') }}</td>
        <td>{{ duplicate.data_source }}</td>
        <td>{{ original.data_source }}</td>
      </tr>
      <tr>
        <td>{{ $t('account.when') }}</td>
        <td><datetime-display :asdate="true" :datetime="duplicate.when" /></td>
        <td><datetime-display :asdate="true" :datetime="original.when" /></td>
      </tr>
      <tr>
        <td>{{ $t('account.source.number') }}</td>
        <td><account-number-display :number="duplicate.source ? duplicate.source.number : null"/></td>
        <td><account-number-display :number="original.source ? original.source.number : null"/></td>
      </tr>
      <tr>
        <td>{{ $t('account.source.name') }}</td>
        <td><string-or-null-display :value="duplicate.source ? duplicate.source.name : null"></string-or-null-display></td>
        <td><string-or-null-display :value="original.source ? original.source.name : null"></string-or-null-display></td>
      </tr>
      <tr>
        <td>{{ $t('account.dest.number') }}</td>
        <td><account-number-display :number="duplicate.dest ? duplicate.dest.number : null"/></td>
        <td><account-number-display :number="original.dest ? original.dest.number : null"/></td>
      </tr>
      <tr>
        <td>{{ $t('account.dest.name') }}</td>
        <td><string-or-null-display :value="duplicate.dest ? duplicate.dest.name : null"></string-or-null-display></td>
        <td><string-or-null-display :value="original.dest ? original.dest.name : null"></string-or-null-display></td>
      </tr>
      <tr>
        <td>{{ $t('amount') }}</td>
        <td><currency-display :currency="duplicate.currency" :amount="getAmountWithCurrency(duplicate.amount)" :do-color="false"></currency-display></td>
        <td><currency-display :currency="original.currency" :amount="getAmountWithCurrency(original.amount)" :do-color="false"></currency-display></td>
      </tr>
      <tr v-for="key in commonMetadataKeys" :key="key">
        <td>{{ humanReadable(key) }}</td>
        <td><string-or-null-display :value="duplicate.metadata_[key]" /></td>
        <td><string-or-null-display :value="original.metadata_[key]" /></td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Transaction from '@/utils/api/Transaction';
import AccountNumberDisplay from '@/components/generic/AccountNumberDisplay';
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay';
import DatetimeDisplay from '@/components/generic/DatetimeDisplay';
import CurrencyDisplay from '@/components/generic/CurrencyDisplay';
import { strcurrency } from '@/utils/helpers';


export default defineComponent({
  components: {
    AccountNumberDisplay,
    StringOrNullDisplay,
    DatetimeDisplay,
    CurrencyDisplay
  },
  name: 'DuplicateComparisonTable',
  props: {
    duplicateTransaction: {
      type: Transaction,
      required: true,
    }
  },
  computed: {
    original() {
      return this.duplicateTransaction.is_duplicate_of;
    },
    duplicate() {
      return this.duplicateTransaction;
    },
    commonMetadataKeys() {
      let duplicateKeys = Object.keys(this.duplicate.metadata_);
      let originalKeys = Object.keys(this.original.metadata_);
      return Array.from(new Set([...duplicateKeys, ...originalKeys])).sort();
    }

  },
  methods: {
    getAmountWithCurrency(amount) {
      return strcurrency(amount);
    },
    humanReadable(s) {
      if (s) {
        return (s.charAt(0).toUpperCase() + s.slice(1)).replaceAll("_", " ");
      } else {
        return "";
      }
    },
  }
});

</script>