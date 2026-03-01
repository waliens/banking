<template>
  <string-or-null-display :value="formattedAccountNumber" ></string-or-null-display >
</template>
  
<script>
import { defineComponent } from '@vue/composition-api'
import StringOrNullDisplay from './StringOrNullDisplay.vue';
import {formatAccountNumber} from '@/utils/helpers';
  
export default defineComponent({
  components: { StringOrNullDisplay },
  props: {
    number: String,
  },
  computed: {
    formattedAccountNumber() {
      return formatAccountNumber(this.number);
    }
  }
})
</script>
  
<style lang="scss" scoped>
</style>
  