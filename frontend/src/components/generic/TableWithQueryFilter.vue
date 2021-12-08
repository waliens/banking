<template>
  <div>
    <section>
      <div class="field is-grouped">
        <div class="control">
          <b-field :label="$t('search')">
            <b-input v-model="query"></b-input>
          </b-field>
        </div>
      </div>
    </section>
    <section>
      <b-table :data="filtered" :columns="columns"></b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  props: { 
    'data': Array, 
    'filter_from_query': Function, 
    'columns': Object
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
      return this.filter_from_query(this.query, this.data);
    }
  }
})
</script>

<style lang="scss" scoped>

</style>