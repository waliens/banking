<template>
  <b-menu-item @click="() => clicked(category)" :icon="category.icon" :expanded="hasChildrenCategories || hasAddButton" >
    <template #label>
      <span class="icon"><i class="fas fa-circle" :style="`color: ${category.color}`"></i></span> 
      {{category.name}} 
      <b-icon v-if="hasChildrenCategories || hasAddButton" class="is-pulled-right" :icon="expanded ? 'chevron-up' : 'chevron-down'"></b-icon>
    </template>
    <div v-if="hasChildrenCategories">
      <category-menu-item 
        v-for="child in category.children" 
        :key="child.id" 
        :category="child" v-model="selected" 
        :include-add-new-button="includeAddNewButton"
        :add-new-handler="addNewHandler"
        :no-select-category="noSelectCategory"
        :depth="depth+1"
        :new-button-max-depth="newButtonMaxDepth">
      </category-menu-item>
    </div>
    <b-menu-item v-if="hasAddButton">
      <template #label>
        <b-field>
          <b-button class="is-primary is-small" @click="() => addNewHandler(category)" icon-left="plus">{{$t('tagging.add_new_category')}}</b-button>
        </b-field>
      </template>
    </b-menu-item>
  </b-menu-item>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Category from '@/utils/api/Category';

export default defineComponent({
  name: 'CategoryMenuItem',
  props: {
    category: {type: Object},
    value: {type: Object},
    includeAddNewButton: {type: Boolean, default: true},
    addNewHandler: {type: Function, default: () => { }},
    noSelectCategory: {type: Category, default: () => new Category()},
    depth: {type: Number, default: 1},
    newButtonMaxDepth: {type: Number, default: 99999}
  },
  data() { 
    return {
      selected: this.value,
      expanded: true
    }; 
  },
  computed: {
    hasAddButton() {
      return this.includeAddNewButton && this.depth < this.newButtonMaxDepth
    },
    hasChildrenCategories() {
      return this.category.children.length > 0;
    }
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