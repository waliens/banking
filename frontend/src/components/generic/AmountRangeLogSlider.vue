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
      maxValue: 6,  // 10^6
      minValue: 0,  // 10^0 = 1
      defaultRange: [0, 6],
      step: 0.003, // 3 / 1000 (change of scale at 10^3)
    };
  },
  computed: {
    range: {
      get() {
        let range = !this.value ? this.defaultRange : this.value;
        return range.map(this.convertAmountToSlider)
      },
      set(value) {
        this.$emit('input', value.map(this.convertSliderToAmount));
      }
    }
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
  }
})
</script>

<style scoped>

</style>