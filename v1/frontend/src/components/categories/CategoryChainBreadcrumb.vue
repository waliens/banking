<template>
  <div>
    <b-breadcrumb size="is-small" v-if="parentCategoryId && chain.length > 0" separator="has-succeeds-separator">
      <b-breadcrumb-item v-for="(item, index)  in chain" :key="item.id" :active="true">
        <em v-if="index == chain.length - 1">{{item.name}}</em>
        <p v-else>{{item.name}}</p>
      </b-breadcrumb-item>
    </b-breadcrumb>
    <p v-else>{{$t('tagging.tag.no_parent')}}</p>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: {
    categoryTree: {type: Array}, 
    parentCategoryId: {type: Number}
  },
  computed: {
    chain() {
      if (!this.parentCategoryId) {
        return [];
      }
      let path = this.treePath(this.categoryTree, this.parentCategoryId);
      if (!path) {
        return [];
      } else {
        return path;
      }
    }
  },
  methods: {
    treePath(nodes, categoryId) {
      if (!nodes || nodes.length == 0) {
        return null;
      }
      for (let idx in nodes) {
        let node = nodes[idx];
        if (node.id == categoryId) {
          return [node];
        }
        let found = this.treePath(node.children, categoryId);
        if (found) {
          return [node, ...found]
        }
      }
      return null;
    }
  }

})
</script>
