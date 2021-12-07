<template>
    <b-navbar>
         <template #brand>
            <b-navbar-item tag="router-link" :to="{ path: '/' }">
              Banking
            </b-navbar-item>
        </template>
        <template #end>
          {{group}}
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
          return this.$t("group not selected");
        }
      }
    }
})
</script>

<style lang="scss">

</style>