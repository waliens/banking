<template>
  <b-navbar :fixed-top="true" :transparent="false" class="is-primary">
    <template #brand>
      <b-navbar-item tag="router-link" :to="{ path: '/' }">
        {{$t("app_name")}}
      </b-navbar-item>
    </template>
    <template #end>
        <b-navbar-item tag="div">
          <div class="group info">
            <b-tag :type="tag_class">{{group}}</b-tag>
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
      if (this.$store.group) {
        return this.$store.group.name;
      } else{
        return this.$t("account_group.not_selected");
      }
    },
    tag_class() {
      if (this.$store.group) {
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