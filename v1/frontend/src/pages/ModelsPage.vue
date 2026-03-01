<template>
  <div>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('ml_model.title')}}</h3></div>
      <div class="level-right">
        <b-button v-on:click="refreshSourceModel" icon-right="redo" class="is-secondary" :disabled="refreshDisabled">{{$t('ml_model.refresh')}}</b-button>
        </div>
    </section>
    <section>
      <b-table
        :loading="isLoading"
        :data="modelFiles">

        <b-table-column field="state" :label="$t('ml_model.state')" v-slot="props" sortable>
          <b-tag :class="getStateClass(props.row.state)">{{props.row.state}}</b-tag>
        </b-table-column>

        <b-table-column field="metadata" :label="$t('ml_model.metadata')" v-slot="props" sortable>
          <p>{{formatMetadata(props.row.metadata)}}</p>
        </b-table-column>
      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import MLModelFile from '@/utils/api/MLModelFile';

export default defineComponent({
  data() {
    return {
      refreshDisabled: false,
      modelFiles: [],
      isLoading: false
    };
  },
  async created() {
    await this.getModeFiles();
  },
  methods: {
    async getModeFiles() {
      this.isLoading = true;
      this.modelFiles = await MLModelFile.fetchAll();
      this.isLoading = false;
    },
    getStateClass(state) {
      return {
        invalid: "is-warning",
        valid: "is-success",
        training: "is-primary",
        deleted: "is-light",
        unknown: ""
      }[state.toLowerCase()];
    },
    formatMetadata(metadata) {
      return JSON.stringify(metadata);
    },
    async refreshSourceModel() {
      this.refreshDisabled = true;
      MLModelFile.refresh().then(() => {
        this.$buefy.toast.open({
          message: this.$t('ml_model.refresh_success'),
          hasIcon: true,
          type: 'is-success'
        });
      }).catch(e => {
        this.$buefy.toast.open({
          message: this.$t('ml_model.refresh_failure', {msg: e}),
          hasIcon: true,
          type: 'is-danger'
        });
        setTimeout(() => this.refreshDisabled = false, 1000);
      });
    }
  }
})
</script>

<style lang="scss" scoped>

</style>