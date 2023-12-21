<template>
  <div>
    <b-loading :is-full-page="true" :active="loading"/>
    <section class="level title-section">
      <div class="level-left"><h3 class="level-item title">{{$t('data_upload.title')}}</h3></div>
      <div class="level-right">
        <b-button v-if="isMastercardPdf() && files.length > 0" v-on:click="triggerMastercardPreview" class="level-item is-small" icon-right="search">{{$t('preview')}}</b-button>
        <b-button v-on:click="submitFiles" class="level-item is-small" icon-right="upload" :disabled="isMastercardPdf() && !mastercardAccount">{{$t('upload')}}</b-button>
      </div>
    </section>
    <section>
      <b-field :label="$t('data_upload.upload_file_type')" label-position="on-border">
        <b-select v-model="uploadFormat" expanded class="is-primary">
           <option v-for="option in uploadFormats" :key="option.id" :value="option.id" :expanded="false">{{option.name}}</option>
        </b-select>
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
    <section v-if="isMastercardPdf()" class="mscard-section">
      <account-drop-down-selector :label="$t('data_upload.mastercard_account')" :accounts="accounts" v-model="mastercardAccount" horizontal/>
      <b-table 
        v-if="mastercardPreview" 
        :data="mastercardPreview" >

        <b-table-column :label="$t('account.name')" v-slot="props">
          <div v-if="props.row.account"><string-or-null-display :value="props.row.account.name"></string-or-null-display> / <string-or-null-display :value="props.row.account.number"></string-or-null-display></div>
          <div v-else><p>{{props.row.account_name}}</p></div>      
        </b-table-column>

        <b-table-column v-slot="props"> 
          <b-tag v-if="!props.row.account" class="is-primary is-small">New</b-tag> 
        </b-table-column>

        <b-table-column :label="$t('date')" v-slot="props">
          <datetime-display :datetime="props.row.when" :asdate="true"></datetime-display>
        </b-table-column>

        <b-table-column :label="$t('amount')" v-slot="props">
          <currency-display :currency="props.row.currency" :amount="props.row.amount" :doColor="true"></currency-display>
        </b-table-column>

        <b-table-column v-slot="props">
          <b-tooltip v-if="props.row.duplicate" :label="$t('data_upload.duplicate')" class="is-danger" ><b-icon icon="copy" type="is-danger"></b-icon></b-tooltip>
        </b-table-column>

      </b-table>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import Model from '@/utils/api/Model';
import Account from '@/utils/api/Account';
import AccountDropDownSelector from '../components/accounts/AccountDropDownSelector.vue';
import TableWithQueryFilter from '../components/generic/TableWithQueryFilter.vue';
import StringOrNullDisplay from '../components/generic/StringOrNullDisplay.vue';
import CurrencyDisplay from '../components/generic/CurrencyDisplay.vue';
import DatetimeDisplay from '../components/generic/DatetimeDisplay.vue';

export default defineComponent({
  components: { AccountDropDownSelector, TableWithQueryFilter, StringOrNullDisplay, CurrencyDisplay, DatetimeDisplay},
  data() {
    return {
      loading: false,
      files: [],
      accounts: [],
      uploadFormats: [
        {id: "belfius", name: "Belfius / CSV"},
        {id: "mastercard_pdf", name: "Mastercard / PDF"}
      ],
      uploadFormat: "belfius",
      mastercardAccount: null,
      mastercardPreview: null,
      mastercardTable: {
        columns: [
        ],
        queryFilter: () => []
      }
    };
  },
  methods: {
    deleteDropFile(index) {
      this.files.splice(index, 1);
    },
    async submitFiles(){
      let args = {'format': this.uploadFormat};
      if (this.isMastercardPdf()) {
        args.id_mscard_account = this.mastercardAccount.id;
      }
      await Model.uploadFiles(this.files, "/upload_files", args).then(() => {
        this.$router.push({name: 'dashboard'});
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
    },
    isMastercardPdf() {
      return this.uploadFormat == 'mastercard_pdf';
    },
    async getAccounts() {
      return await Account.fetchAll();
    },
    async triggerMastercardPreview() {
      let previewData = await Model.uploadFiles(this.files, "/upload_files", {'format': 'mastercard_pdf_preview'});
      this.mastercardPreview = previewData.data;
    }
  },
  watch: {
    uploadFormat: async function (value) {
      if (value == "mastercard_pdf") {
        this.loading = true;
        this.accounts = await this.getAccounts();
        this.loading = false;
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.mscard-section {
  margin-top: 10px;
}
</style>