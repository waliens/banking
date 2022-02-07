<template>
  <div class="columns"> 
    <section class="column is-one-quarter">
      <b-menu class="scrollable">
        <b-menu-list :label="$t('tagging.tree')">
          <category-menu-item v-for="root in tree" :key="root.id" :category="root" v-model="selected"></category-menu-item>
        </b-menu-list>
      </b-menu>
    </section>
    <section class="column">
      <section class="level title-section">
        <div class="level-left"><h3 class="level-item title">{{$t('category')}}</h3></div>
        <div class="level-right">
          <b-button v-if="selected.id" class="level-item is-small is-danger" @click="() => {}" icon-right="times">{{$t('delete')}}</b-button>
          <b-button :disabled="!isFormValid()" class="level-item is-small is-primary" @click="() => {}" icon-right="pen">{{$t('save')}}</b-button>
        </div>
      </section>
      <section>
        <b-field :label="$t('tagging.tag.name')" label-position="on-border">
          <b-input v-model="selected.name"></b-input>
        </b-field>
        <b-field :label="$t('tagging.tag.color')" label-position="on-border">
          <b-input v-model="selected.color"></b-input>
        </b-field>
        <b-field :label="$t('tagging.tag.icon')" label-position="on-border">
          <b-input v-model="selected.icon"></b-input>
        </b-field>
        <b-field>
          <b-checkbox v-model="selected.income">{{$t('tagging.tag.default')}}</b-checkbox>
        </b-field>
        <b-field>
          <b-checkbox v-model="selected.income">{{$t('tagging.tag.income')}}</b-checkbox>
        </b-field>
        <b-field :label="$t('tagging.tag.parents')" horizontal position="is-left">
          <category-chain-breadcrumb :category-tree="tree" :parent-category-id="selected.id_parent"></category-chain-breadcrumb>
        </b-field>
      </section>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Category from '@/utils/api/Category';
import CategoryMenuItem from '@/components/categories/CategoryMenuItem';
import CategoryChainBreadcrumb from '@/components/categories/CategoryChainBreadcrumb';

export default defineComponent({
  components: {CategoryMenuItem, CategoryChainBreadcrumb},
  name: "edit-tag-tree-page",
  data() {
    return {
      tree: [],
      selected: new Category()
    };
  },
  async created() {
    this.tree = await Category.getCategoryTree();
  },
  methods: {
    isFormValid() {
      return false;
    }
  }
})
</script>

<style lang="scss" scoped>
@import "@/assets/colors.scss";
.scrollable {
  max-height: 100vh;
  overflow-y: auto;
}
</style>