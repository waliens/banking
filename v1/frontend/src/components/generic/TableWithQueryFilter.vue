<template>
  <div>
    <section class="level">
      <div class="level-left" v-if="title"><h3 class="subtitle">{{title}}</h3> </div>
      <div class="level-right"><b-field class="level-item" :label="$t('search')" label-position="on-border"><b-input v-model="query"></b-input></b-field></div>
    </section>
    <section>
      <b-table 
        :data="filtered" 
        :checkable="selectable" 
        :checked-rows.sync="checked"
        :is-row-checkable="isItemSelectable">

        <b-table-column v-for="col in columns" v-bind:key="col.field" v-slot="props" v-bind="col">
          <slot :name="col.field" v-bind="props"><span v-if="props.row.hasOwnProperty(col.field)">{{props.row[col.field]}}</span></slot>
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
    'title': String
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
section.level:not(:last-child){
  margin-bottom: 5px;
}
</style>