<template>
  <div>
    <section>
      <div class="field is-grouped">
        <b-field :label="$t('search')" label-position="on-border">
          <b-input v-model="query"></b-input>
        </b-field>
      </div>
    </section>
    <section>
      <b-table 
        :data="filtered" 
        :columns="columns" 
        :checkable="selectable" 
        :checked-rows.sync="selected"
        :is-row-checkable="isItemSelectable"></b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: { 
    'data': { type: Array, default: [] },  
    'columns': Array,
    'filterFromQuery': { type: Function, default: () => true }, 
    'isItemSelectable': { type: Function, default: () => true },
    'selectable': { type: Boolean, default: false },
    'selected': { type: Array, default: [] }
  },
  data() {
    return {
      query: ""
    }
  },
  computed: {
    filtered() {
      if (!this.query || this.query.length == 0) {
        return this.data;
      }
      return this.filterFromQuery(this.query, this.data);
    }
  }
})
</script>

<style lang="scss" scoped>

</style>