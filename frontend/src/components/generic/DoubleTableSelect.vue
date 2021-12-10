<template>
  <div class="columns">
    <div class="column is-one-tenth">
      <table-with-query-filter
        :data="selected"
        :filter-from-query="filterFromQuery"
        :columns="columns"
        :selectable="true"
        :selected="leftSelected"
        ></table-with-query-filter>
    </div>
    <div class="buttons column is-narrow">
      <b-button type="is-info" v-on:click="toLeft"><i class="fas fa-chevron-left"></i></b-button><br />
      <b-button type="is-info" v-on:click="toRight"><i class="fas fa-chevron-right"></i></b-button>
    </div>
    <div class="column">
      <table-with-query-filter
        :data="notSelected"
        :filter-from-query="filterFromQuery"
        :columns="columns"
        :selectable="true"
        :selected="rightSelected"
        ></table-with-query-filter>
    </div>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api';
import TableWithQueryFilter from '@/components/generic/TableWithQueryFilter';

export default defineComponent({
  components: { TableWithQueryFilter },
  props: {
    'notSelected': Array,
    'selected': Array,
    'filterFromQuery': Function,
    'columns': Array 
  },
  data() {
    return {
      leftSelected: [],
      rightSelected: []
    };
  },
  methods: {
    toRight() {

    },
    toLeft() {

    }
  }
})
</script>

<style lang="scss" scoped>

</style>