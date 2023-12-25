<template>
  <div class="columns"> 
    <section class="column is-one-quarter">
      <b-menu :activable="false" class="scrollable">
        <b-menu-list>
          <template #label>
            <div class="level">
              <p class="level-item level-left">{{ $t('tagging.tree') }}</p>
              <b-field grouped class="level-right category-tree-buttons-level">
                <b-field class="level-item">
                  <b-button class="is-small" icon-left="plus" @click="selected = getDefaultCategory()"></b-button>
                </b-field>
              </b-field>
            </div>
          </template> 
          <category-menu-item v-for="root in tree" :key="root.id" :category="root" v-model="selected" :add-new-handler="newCategory" :no-select-category="getDefaultCategory()" :new-button-max-depth="2"></category-menu-item>
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
          <p class="control"><b-button icon-left="times" @click="selected.id_parent = null"></b-button></p>
        </b-field>
        <div class="level"> 
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
      return Category.getStringBreadcrumbs(this.tree);
    }
  },
  methods: {
    isFormValid() {
      return this.selected.name && this.selected.name.length > 0
        && this.selected.icon
        && this.selected.color
        && this.selected.id_parent;
    },
    async saveCategory() {
      await this.successFailureToast(this.selected.save());
      await this.refreshTree();
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
    async refreshTree() {
      this.tree = await Category.getCategoryTree();
    },
    async refreshPage() {
      await this.refreshTree();
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

.category-tree-buttons-level {
  margin-right: 10px;
}
</style>