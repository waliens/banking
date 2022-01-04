<template>
  <div class="columns">
    <div class="column is-one-tenth">
      <table-with-query-filter
        :checked.sync="leftChecked"
        :data="left"
        :filter-from-query="filterFromQuery"
        :columns="columns"
        :selectable="true"
        :title="titleSelected"
        ></table-with-query-filter>
    </div>
    <div class="buttons column is-narrow">
      <b-button type="is-info" v-on:click="toLeft"><i class="fas fa-chevron-left"></i></b-button><br />
      <b-button type="is-info" v-on:click="toRight"><i class="fas fa-chevron-right"></i></b-button>
    </div>
    <div class="column">
      <table-with-query-filter
        :checked.sync="rightChecked"
        :data="right"
        :filter-from-query="filterFromQuery"
        :columns="columns"
        :selectable="true"
        :title="titleNotSelected"
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
    'data': Array,
    'selected': Array,  // of identifiers
    'keyFn': Function,  // function to apply to items of data to extract an identifier
    'filterFromQuery': Function,
    'columns': Array,
    'titleSelected': String,
    'titleNotSelected': String,
    'maxSelected': { type: Number, default: -1 } 
  },
  data() {
    return {
      leftChecked: [],
      rightChecked: []
    };
  },
  computed: {
    left() {
      return this.data.filter(e => this.selectedSet.has(this.keyFn(e)));
    },
    right() {
      return this.data.filter(e => !this.selectedSet.has(this.keyFn(e)));
    },
    selectedSet() {
      return new Set(this.selected.map(this.keyFn));
    }
  },
  methods: {
    toRight() {
      if (this.leftChecked.length == 0) {
        this.toastError(this.$t('double-table-select.nothing-selected'));
        return
      }
      let newSelected = new Array();
      let removeSet = new Set(this.leftChecked.map(e => this.keyFn(e)));
      newSelected.push(...this.selected.filter(e => !removeSet.has(this.keyFn(e))));
      this.resetChecks();
      this.$emit('update:selected', newSelected);
    },
    toLeft() {      
      if (this.rightChecked.length == 0) {
        this.toastError(this.$t('double-table-select.nothing-selected'));
        return
      }
      let newSelected = new Array();
      let selectedSet = this.selectedSet;
      /*
       When maxSelected is set to 1, automatically replace the selected element calling toLeft.
      */
      if (this.maxSelected > 1 && (this.rightChecked.length + this.selected.length) > this.maxSelected) {
        this.toastError(this.$t('double-table-select.selected-too-many', {selected: this.rightChecked.length + this.selected.length, max: this.maxSelected}));
        return;
      }
      if (this.maxSelected == 1 && this.rightChecked.length > 1) {
        this.toastError(this.$t('double-table-select.selected-too-many', {selected: this.rightChecked.length, max: this.maxSelected}));
        return;
      }
      
      if (this.maxSelected > 1) {
        newSelected.push(...this.selected);
      }
      newSelected.push(...this.rightChecked.filter(e => !selectedSet.has(this.keyFn(e))));
  
      this.resetChecks();
      this.$emit('update:selected', newSelected);
    },
    resetChecks() {
      console.log("reset");
      this.rightChecked.splice(0, this.rightChecked.length);
      this.leftChecked.splice(0, this.leftChecked.length);
    },
    toastError(msg) {
      this.$buefy.toast.open({
        message: msg,
        type: 'is-danger'
      });
    }
  }
})
</script>

<style lang="scss" scoped>

</style>