<template>
  <div>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('ml_model.title')}}</h3></div>
      <div class="level-right">
        <!-- <b-button v-if="selectedAccountGroup" class="level-item is-small is-secondary" v-on:click="selectGroup">{{$t('select')}}</b-button>
        <b-button v-on:click="goToCreateGroup" class="level-item is-small" icon-right="plus">{{$t('account_group.create_account_group')}}</b-button> -->
      </div>
    </section>
    <section>
      <b-field :label="$t('ml_model.target')" label-position="on-border" >
        <b-select v-model="selectedDataSource" expanded>
          <option 
            v-for="source in dataSources"
            :key="source"
            :value="source">
            {{ source }}
          </option>
        </b-select>
        <p class="control">
          <b-button v-on:click="refreshSourceModel" icon-right="redo" class="is-secondary" :disabled="refreshDisabled">{{$t('ml_model.refresh')}}</b-button>
        </p>
      </b-field>
    </section>
    <section>
      <b-table
        :loading="isLoading"
        :data="modelFiles">

        <b-table-column field="target" :label="$t('ml_model.target')" v-slot="props" sortable>
          {{props.row.target}}
        </b-table-column>
        
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
      selectedDataSource: 'belfius',
      dataSources: ['belfius'],  // mastercard not available yet
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
      MLModelFile.refresh(this.selectedDataSource).then(() => {
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