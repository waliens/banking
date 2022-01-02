<template>
    <div>
      <h1 class="title">Group <em>{{group.name}}</em></h1>
      <section>
        <account-table :accounts="group.accounts"></account-table>
      </section>
    </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import AccountTable from '../components/accounts/AccountTable.vue';

export default defineComponent({
  components: {AccountTable},
  setup() {
    console.log(this.$store.currentGroup);
  },
  computed: {
    group() {
      return this.$store.state.currentGroup;
    } 
  }
})
</script>

<style lang="scss">

</style>