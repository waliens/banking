<template>
    <div>home {{ group.name }}</div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  setup() {
    console.log(this.$store.currentGroup);
  },
  computed: {
    group() {
      return this.$store.state.currentGroup;
    } 
  }
})
</script>

<style lang="scss">

</style>