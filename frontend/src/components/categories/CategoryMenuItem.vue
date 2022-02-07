<template>
  <b-menu-item @update:active="() => clicked(category)" :icon="category.icon" :active="!!selected && selected.id == category.id" :expanded="expanded">
    <template #label>
      {{category.name}}
      <b-icon class="is-pulled-right" :icon="expanded ? 'menu-up' : 'menu-down'"></b-icon>
    </template>
    <div v-if="category.children.length > 0">
      <category-menu-item v-for="child in category.children" :key="child.id" :category="child" v-model="selected"></category-menu-item>
    </div>
  </b-menu-item>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  name: 'CategoryMenuItem',
  props: {
    'category': {type: Object},
    'value': {type: Object}
  },
  data() { 
    return {
      selected: this.value,
      expanded: true
    }; 
  },
  methods: {
    clicked(category) {
      this.$emit("input", category);
    }
  },
  watch: {
    selected(newCategory, oldCategory) { 
      if (newCategory != oldCategory) {
        this.$emit("input", newCategory);
      }
    },
    value(newValue, oldValue) {
      if (newValue != oldValue) {
        this.selected = newValue;
      }
    }
  }
})
</script>
