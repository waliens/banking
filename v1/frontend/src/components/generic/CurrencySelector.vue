<template>
  <b-select v-model="selected" :size="size" :expanded="expanded">
    <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
      <p>{{currency.long_name }} ({{ currency.symbol }})</p>
    </option>
  </b-select>
</template>

<script>
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    currencies: {type: Array}, 
    value: {type: Number},
    size: {type: String, default: ""},
    expanded: {type: Boolean, default: false}
  },
  data() {
    return {
      selected: this.value
    }
  },
  watch: {
    selected() {
      this.$emit('input', this.selected);
    }
  }
});
</script>
