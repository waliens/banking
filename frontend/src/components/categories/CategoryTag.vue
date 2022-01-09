<template>
  <div>
     <p v-if="category"><b-tooltip class="is-primary" :label="category.name"><b-icon :icon="category.icon" :style="style"></b-icon></b-tooltip></p>
     <p v-if="!category"><string-or-null-display :value="null"></string-or-null-display></p>
  </div>  
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import StringOrNullDisplay from '@/components/generic/StringOrNullDisplay'

export default defineComponent({
  components: { StringOrNullDisplay  },
  props: {
    category: { type: Object },
    useTagColor: {type: Boolean, default: false }
  },
  computed: {
    color() {
      if (this.useTagColor) {
        return this.category.color;
      } else {
        return this.category.income ? "#63BE7B" : "#F8696B";
      }
    },
    style() {
      return "color: " + this.color + ";"
    }
  }
})
</script>

<style scoped>

</style>