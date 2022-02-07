<template>
  <b-menu-item @update:active="() => clicked(category)" :icon="category.icon" :active="!!selected && selected.id == category.id" :expanded="category.children.length > 0 && expanded">
    <template #label>
      {{category.name}}
      <b-icon class="is-pulled-right" :icon="expanded ? 'chevron-up' : 'chevron-down'"></b-icon>
    </template>
      <div v-if="category.children.length > 0">
        <category-menu-item 
          v-for="child in category.children" 
          :key="child.id" 
          :category="child" v-model="selected" 
          :include-add-new-button="includeAddNewButton"
          :add-new-handler="addNewHandler">
        </category-menu-item>
      </div>
      <b-menu-item v-if="includeAddNewButton">
        <template #label>
          <b-field>
            <b-button class="is-primary is-small" @click="() => addNewHandler(category)" icon-left="plus">{{$t('tagging.add_new_category')}}</b-button>
          </b-field>
        </template>
      </b-menu-item>
  </b-menu-item>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  name: 'CategoryMenuItem',
  props: {
    category: {type: Object},
    value: {type: Object},
    includeAddNewButton: {type: Boolean, default: true},
    addNewHandler: {type: Function, default: () => { }}
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
