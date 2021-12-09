<template>
  <section>
    <b-field>
      <b-button v-on:click="submitFiles" expanded class="is-primary">
          <b-icon icon="upload"></b-icon>
          <span>{{$t("upload")}}</span>
      </b-button>
    </b-field>
    <b-field>
      <b-upload v-model="files" multiple drag-drop expanded>
        <section class="section">
          <div class="content has-text-centered">
            <p>
              <b-icon icon="upload" size="is-large"></b-icon>
            </p>
            <p>{{$t("drop_or_upload")}}</p>
          </div>
        </section>
      </b-upload>
    </b-field>

    <div class="tags">
      <span v-for="(file, index) in files" :key="index" class="tag is-primary">
        {{file.name}}
        <button class="delete is-small" type="button" @click="deleteDropFile(index)"></button>
      </span>
    </div>
  </section>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Model from '@/utils/api/Model';

export default defineComponent({
  data() {
    return {
      files: []
    };
  },
  methods: {
    deleteDropFile(index) {
      this.files.splice(index, 1);
    },
    async submitFiles(){
      await Model.uploadFiles(this.files, "/upload_files", {'format': 'belfius'}).then(() => {
        this.$router.push({name: 'home'});
      }).catch(err => {
        this.$buefy.dialog.alert({
          title: 'Error',
          message: 'Could not upload the files: ' + err.message,
          type: 'is-danger',
          hasIcon: true,
          icon: 'times-circle',
          iconPack: 'fa',
          ariaRole: 'alertdialog',
          ariaModal: true
        });
      });
    }
  }
})
</script>

<style lang="scss" scoped>

</style>