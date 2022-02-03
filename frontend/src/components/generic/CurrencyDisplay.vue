<template>
  <span :class="colorClass">{{formattedAmount}}</span>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import currency from "currency.js";
import { strcurrency } from '@/utils/helpers';

export default defineComponent({
  props: {
    'currency': Object,
    'amount': {},
    'doColor': {type: Boolean, default: false}
  },
  computed: {
    formattedAmount() {
      // parse
      let parsed = strcurrency(this.amount);

      // prepare formatting
      let formatFmtObj = { 
        precision: 2, 
        decimal: ',',
        separator: ' ',
        negativePattern: '! -#',
        pattern: '! #'
      };

      if (this.currency instanceof String) {
        formatFmtObj.symbol = this.currency;
      } else if ('symbol' in this.currency) {
        formatFmtObj.symbol = this.currency.symbol;
      }

      return currency(parsed, formatFmtObj).format();
    },
    colorClass() {
      if (!this.doColor) {
        return "";
      }
      let amount = strcurrency(this.amount);
      if (amount.value >= 0) {
        return "amountPositive";
      } else {
        return "amountNegative";
      }
    }
  }
})
</script>

<style lang="scss" scoped>
@import "@/assets/colors.scss";
.amountNegative {
  color: $amount-negative;
}
.amountPositive {
  color: $amount-positive;
}
</style>