<template>
  <b-navbar class="is-primary">
    <template #brand>
      <b-navbar-item tag="router-link" :to="{ name: 'home' }">
        {{$t("app_name")}}
      </b-navbar-item>
    </template>
    <template #start>
      <b-navbar-item tag="router-link" :to="{ name: 'merge-accounts' }">
        {{$t('account.merge')}}
      </b-navbar-item>
    </template>
    <template #end>
        <b-navbar-item tag="router-link" :to="{ name: 'select-account-group' }">
          <div class="group info">
            <b-tag :type="tag_class">Group: <em>{{!!group ? group.name : $t('account_group.not_selected')}}</em></b-tag>
          </div>
        </b-navbar-item>
    </template>
  </b-navbar>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    tag_class() {
      if (this.group) {
        return "is-success";
      } else{
        return "is-warning";
      }
    }
  }
})
</script>

<style lang="scss">
@import "@/assets/colors.scss";
#brand, #end {
  background-color: $primary;
}
</style>