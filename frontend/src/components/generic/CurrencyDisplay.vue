<template>
  <span :class="colorClass">{{formattedAmount}}</span>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import currency from "currency.js";
import { strcurrency } from '@/utils/helpers';

export default defineComponent({
  props: {
    'currency': {},
    'amount': {},
    'doColor': {type: Boolean, default: false},
    'reduceAlphaOnZero': {type: Boolean, default: false}
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
      
      if (typeof this.currency === 'string') {
        formatFmtObj.symbol = this.currency;
      } else {
        formatFmtObj.symbol = this.currency.symbol;  
      }

      return currency(parsed, formatFmtObj).format();
    },
    colorClass() {
      let amount = strcurrency(this.amount);
      if (amount.value == 0) {
        if (this.reduceAlphaOnZero) {
          return "amountZero";
        } else {
          return "";
        }
      } else if (this.doColor){
        if (amount.value > 0) {
          return "amountPositive";
        } else {
          return "amountNegative";
        }
      } else {
        return "";
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

// reduce alpha on zero
.amountZero {
  color: rgba(black, 0.25);
}

</style>