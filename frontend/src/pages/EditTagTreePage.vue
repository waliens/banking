<template>
  <div class="columns"> 
    <section class="column is-one-quarter">
      <b-menu :activable="false" class="scrollable">
        <b-menu-list :label="$t('tagging.tree')">
          <category-menu-item v-for="root in tree" :key="root.id" :category="root" v-model="selected" :add-new-handler="newCategory" :no-select-category="getDefaultCategory()"></category-menu-item>
        </b-menu-list>
      </b-menu>
    </section>
    <section class="column">
      <section class="level title-section">
        <div class="level-left">
          <h3 class="level-item title">{{$t('category')}}</h3>
        </div>
        <div class="level-right">
          <b-button v-if="selected.id" class="level-item is-small is-danger" @click="deleteWarning" icon-right="times">{{$t('delete')}}</b-button>
          <b-button :disabled="!isFormValid()" class="level-item is-small is-primary" @click="saveCategory" icon-right="pen">{{$t('save')}}</b-button>
        </div>
      </section>
      <section>
        <div class="breadcrumb">
          <category-chain-breadcrumb :category-tree="tree" :parent-category-id="selected.id_parent"></category-chain-breadcrumb>
        </div>
        <b-field :label="$t('tagging.tag.name')" label-position="on-border">
          <b-input v-model="selected.name"></b-input>
        </b-field>
        <b-field :label="$t('tagging.tag.icon')" label-position="on-border">
          <b-input v-model="selected.icon"></b-input>
        </b-field>
        <b-field :label="$t('tagging.tag.parent')" label-position="on-border" >
          <b-select v-model="selected.id_parent" expanded>
            <option v-for="chain in allStringBreadcrumbs" :key="chain.id" :value="chain.id">
              {{chain.breadcrumb}}
            </option>
          </b-select>
        </b-field>
        <div class="level"> 
          <b-field class="level-item">
            <b-checkbox v-model="selected.default">{{$t('tagging.tag.default')}}</b-checkbox>
          </b-field>
          <b-field class="level-item">
            <b-checkbox v-model="selected.income">{{$t('tagging.tag.income')}}</b-checkbox>
          </b-field>
          <b-field class="level-item" :label="$t('tagging.tag.color')" horizontal narrowed>
            <verte v-model="selected.color"
              menuPosition="left"
              picker="square"
              model="hex"
              :enableAlpha="false">
            </verte>
          </b-field>
        </div>
      </section>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import Category from '@/utils/api/Category';
import CategoryMenuItem from '@/components/categories/CategoryMenuItem';
import CategoryChainBreadcrumb from '@/components/categories/CategoryChainBreadcrumb';
import Verte from 'verte';
import 'verte/dist/verte.css';

export default defineComponent({
  components: {CategoryMenuItem, CategoryChainBreadcrumb, Verte},
  name: "edit-tag-tree-page",
  data() {
    return {
      tree: [],
      selected: this.getDefaultCategory()
    };
  },
  async created() {
    await this.refreshPage();
  },
  computed: {
    allStringBreadcrumbs() {
      if (this.tree.length == 0) {
        return [];
      }
      return this.recurGetAllStringBreadcrumbs(this.tree);
    }
  },
  methods: {
    recurGetAllStringBreadcrumbs(nodes) {
      if (nodes.length == 0) {
        return [];
      }
      let currentBreadcrumbs = [];
      for (let nodeIdx in nodes) {
        let node = nodes[nodeIdx];
        let childrenBreadcrumbs = this.recurGetAllStringBreadcrumbs(node.children);

        for (let childBrcmbIdx in childrenBreadcrumbs) {
          let childBrcmb = childrenBreadcrumbs[childBrcmbIdx];
          childBrcmb.breadcrumb = [node.name, childBrcmb.breadcrumb].join(" > ")
          currentBreadcrumbs.push(childBrcmb);
        }
        currentBreadcrumbs.push({id: node.id, breadcrumb: node.name })
      }
      return currentBreadcrumbs;
    },
    isFormValid() {
      return this.selected.name && this.selected.name.length > 0
              && this.selected.icon
              && this.selected.default !== null
              && this.selected.incom !== null
              && this.selected.color
              && this.selected.id_parent;
    },
    async saveCategory() {
      await this.successFailureToast(this.selected.save());
    },
    async deleteCategory() {
      await this.successFailureToast(this.selected.delete());
      await this.refreshPage();
    },
    deleteWarning() {
      this.$buefy.dialog.confirm({
        title: this.$t('tagging.tag_delete_warning.title'),
        message: this.$t(this.selected.children.length > 0 ? 'tagging.tag_delete_warning.with_children' : 'tagging.tag_delete_warning.without_children'),
        cancelText: this.$t('cancel'),
        confirmText: this.$t('confirm'),
        type: 'is-warning',
        hasIcon: true,
        onConfirm: this.deleteCategory
      });
    },
    successFailureToast(promise) {
      return promise.then(() => {
        this.$buefy.toast.open({ message: this.$t('success'), type: 'is-success' });
      }).catch(e => {
        this.$buefy.toast.open({ message: e.message, type: 'is-danger' })
      });
    },
    async refreshPage() {
      this.tree = await Category.getCategoryTree();
      this.selected = this.getDefaultCategory();
    },
    newCategory(parent) {
      let newCategory = this.getDefaultCategory();
      newCategory.id_parent = parent.id;
      this.selected = newCategory;
    },
    getDefaultCategory() {
      let newCategory = new Category();
      newCategory.color = "#000000";
      newCategory.income = false;
      newCategory.default = false;
      newCategory.name = "";
      newCategory.icon = "tag";
      return newCategory;
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

.breadcrumb {
  margin-top: 0;
  margin-bottom: 30px;
}
</style>