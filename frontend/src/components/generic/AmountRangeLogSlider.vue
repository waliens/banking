<template>
  <b-slider 
    v-model="range" 
    :min="minValue" 
    :max="maxValue" 
    :step="step" 
    :customFormatter="formatLabel"
    tooltip-type="is-secondary"
    :expanded="expanded" >
  </b-slider>  
</template>

<script>
import { defineComponent } from '@vue/composition-api'

/**
 * 0 -> 1000: linear
 * 
 */
export default defineComponent({
  name: "AmountRangeLogSlider",
  props: {
    value: {type: Array},
    expanded: {type: Boolean, default: false},
    currencySymbol: {type: String, default: '€'}
  },
  data() {
    return {
      maxValue: 6,
      minValue: 0,
      range: [0, 6],
      step: 0.003, // 3 / 1000 (change of scale at 3)
    };
  },
  methods: {
    convertSliderToAmount(x) {
      if (x < 3) {
        return x * 1000 / 3; 
      } else {
        return Math.pow(10, x);
      }
    },
    convertAmountToSlider(y) {
      if (y < 1000) {
        return y * 3 / 1000;
      } else {
        return Math.log10(y);
      }
    },
    formatLabel(x) {
      return `${this.convertSliderToAmount(x).toFixed(0)} ${this.currencySymbol}`; 
    }
  },
  watch: {
    range(newVal, oldVal) {
      if(newVal.length == 2 && (newVal[0] != oldVal[0] || newVal[1] != oldVal[1])) {
        this.value[0] = this.convertSliderToAmount(newVal[0]);
        this.value[1] = this.convertSliderToAmount(newVal[1]);
      }
    },
    value(newVal, oldVal) {
      if(newVal.length == 2 && (newVal[0] != oldVal[0] || newVal[1] != oldVal[1])) {
        this.range[0] = this.convertAmountToSlider(newVal[0]);
        this.range[1] = this.convertAmountToSlider(newVal[1]);
      }
    }
  }
})
</script>

<style scoped>

</style>