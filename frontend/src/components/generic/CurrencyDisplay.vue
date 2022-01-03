<template>
  <span :class="colorClass">{{formattedAmount}}</span>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import currency from "currency.js";

export default defineComponent({
  props: {
    'currency': Object,
    'amount': Object,
    'doColor': {type: Boolean, default: false}
  },
  computed: {
    formattedAmount() {
      let formatObj = { 
        precision: 2, 
        decimal: ',',
        separator: ' ',
        pattern: '! #'
      };

      if (this.currency instanceof String) {
        formatObj.symbol = this.currency;
      } else if ('symbol' in this.currency) {
        formatObj.symbol = this.currency.symbol;
      }

      return currency(this.amount, formatObj).format();
    },
    colorClass() {
      if (!this.doColor) {
        return "";
      }
      let amount = currency(this.amount);
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