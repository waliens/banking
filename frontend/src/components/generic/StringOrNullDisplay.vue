<template>
  <p>
    <span v-if="text">{{text}}</span>
    <span v-else class="tag">{{$t('undefined')}}</span>
  </p>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: {
    value: String,
    truncate: { type: Number, default: -1 }  // truncate width in pixels
  },
  computed: {
    text() {
      if (!this.value || this.truncate <= 0) {
        return this.value;
      }
      return this.value.slice(0, this.truncate) + "...";
    }
  }
})
</script>

<style lang="scss" scoped>
</style>
