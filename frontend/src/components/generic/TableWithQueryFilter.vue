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
        :checkable="selectable" 
        :checked-rows.sync="checked"
        :is-row-checkable="isItemSelectable">

        <b-table-column v-for="col in columns" v-bind:key="col.field" v-slot="props" v-bind="col">
          <slot :name="col.field" v-bind="props"><span v-if="col.field in props.row">{{props.row[col.field]}}</span></slot>
        </b-table-column>
        
      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: { 
    'data': { type: Array, default: [] },  
    'columns': Array,
    'filterFromQuery': { type: Function }, 
    'isItemSelectable': { type: Function, default: () => true },
    'selectable': { type: Boolean, default: false },
  },
  data() {
    return {
      query: "",
      checked: []
    }
  },
  computed: {
    filtered() {
      if (!this.query || this.query.length == 0) {
        return this.data;
      }
      return this.filterFromQuery(this.query, this.data);
    }
  },
  watch: {
    checked: function(newChecked) {
      this.$emit('update:checked', newChecked);
    }
  }
})
</script>

<style lang="scss" scoped>

</style>