<template>
  <div class="box no-data-box" >
    <h5 class="subtitle">{{$t('charts.no_data')}}</h5>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: {
    width: {type: String},
    height: {type: String}
  }
})
</script>

<style lang="scss" scoped>
@import "@/assets/colors.scss";
.box {
  text-align: center;
  background-color: $placeholder;
  color: $placeholder-text;
  padding: 50px;
}
</style>