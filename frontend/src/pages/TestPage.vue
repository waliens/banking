<template>
  <tabular-summary :group="group" :visible="true" />
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import TabularSummary from '@/components/statistics/TabularSummary';

export default defineComponent({
  components: {TabularSummary},
  computed: {
    group() {
      return this.$store.state.currentGroup;
    }
  }
});
</script>
