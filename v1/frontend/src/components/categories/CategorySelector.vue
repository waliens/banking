<template>
  <b-select :size="size" v-model="selected" :expanded="expanded">
    <optgroup v-for="top_level in categories" :key="top_level.id" :value="top_level.id" :label="top_level.nestedName">
      <option v-for="bottom_level in top_level.children" :key="bottom_level.id" :value="bottom_level.id">
          <p>{{bottom_level.name}}</p>
      </option>
    </optgroup>
  </b-select>
</template>

<script>
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    categories: {type: Array}, 
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
    },
    value() {
      this.selected = this.value;
    }
  }
});
</script>
