<template>
  <div>
    <section>
      <b-menu>
        <b-menu-list :label="$t('tagging.tree')">
          <category-menu-item v-for="root in tree" :key="root.id" :category="root" v-model="selected"></category-menu-item>
        </b-menu-list>
      </b-menu>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Category from '@/utils/api/Category';
import CategoryMenuItem from '@/components/categories/CategoryMenuItem.vue';

export default defineComponent({
  components: {CategoryMenuItem},
  data() {
    return {
      tree: [],
      selected: null
    };
  },
  async created() {
    this.tree = await Category.getCategoryTree();
  }
})
</script>
