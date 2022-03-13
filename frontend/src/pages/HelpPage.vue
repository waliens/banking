<template>
  <div class="content">
    <section>
      <h1 class="title">Help page</h1>
      <h2 class="subtitle">Data upload</h2>
      <p>See <router-link :to="{name: 'upload-data'}">upload page</router-link> </p>
      <p>The app requires that you upload data to work with. Currently, two import file formats are supported: </p>
      <ul>
        <li>Belfius CSV file (more info <a href="https://www.belfius.be/webapps/fr/selfcare/belfius/comptes/solde-historique/Comment-exporter-mon-historique-vers-un-fichier-CSV-(Excel)-en-Belfius-Direct-Net-">here</a>)</li>
        <li>Mastercard spending monthly statement (PDF file from Belfius)</li> 
      </ul>
      <p>
        The upload system should be robust enough to support upload of duplicate transactions. It also attempts to auto-detect and  <br/>
        merge accounts with different names but same number (matching old belgian account numbers with IBAN if necessary). Merging account <br/> 
        is useful for machine learning (see section <em>Machine learning models</em>). Accounts which were not auto-merge can also be <br/>
        merged manually on the <router-link :to="{name: 'merge-accounts'}">merging page</router-link>.
      </p>
      <p>
        As it is not always possible to upload the entire transaction history of an account, its balance will not be equal to its real balance by default. <br/>
        To correct the difference, it is possible to add an <em>initial amount</em> in the account edition page. The amount can be positive or negative.
      </p>
      <p><em>Note:</em> the mastercard PDF upload requires you to also associate the debit account (to which the balance is transferred every month).</p>

      <h2 class="subtitle">Account group</h2>
      <p>See <router-link :to="{name: 'select-account-group'}">account group page</router-link></p>
      <p>
        An account group is a set of accounts. It can be seen as a system with internal transactions and boundary transactions flowing in and out. <br/>
        Some report features on the app will only consider transactions crossing the boundaries of the system (e.g. incomes and expenses).
      </p>
      <p>
        An account group must be created to access the reporting features of the app (it can contain only one account if necessary). <br/>
        After creation, the account group must be selected which gives access to the reporting page. 
      </p>

      <h2 class="subtitle">Reporting</h2>
      <p> See <router-link :to="{name: 'home'}">report (home) page</router-link></p>
      <p>When an account group has been selected, reports regarding this group can be found on the home page including:</p>
      <ul>
        <li>Global balance and list of all accounts of the group (and their balances)</li>
        <li><em>Incomes and expenses charts</em>: only consider boundary transactions</li>
        <li><em>Summary per category</em>: only consider boundary transactions and requires transactions to be labeled (see <em>Labeling transactions</em> section)</li>
      </ul>

      <h2 class="subtitle">Category tree</h2>
      <p>See <router-link :to="{name: 'edit-tag-tree'}">category tree edition page</router-link></p>
      <p>
        Categories can be used to label transactions and unlock different reports per category. The app comes with a default category <br/>
        tree (with names in french) that can be entirely customized on the edition page.
      </p>
      <p>Removing a category or adding a new one invalidates all existing machine learning models (see section <em>Machine learning models</em>).</p>

      <h2 class="subtitle">Labeling transactions</h2>
      <p>See <router-link :to="{name: 'transactions-tagging'}">transactions labeling page</router-link></p>
      <p>
        The app provides a labeling page for making easier to label the uploaded transactions. This page provides a filterable list of transactions <br/>
        and different tools for labeling individual transactions or a batch of transaction. A machine learning model can be used to suggest labels (see section <em>Machine learning models</em>).
      </p> 
      <p>Tips for faster labeling:</p>
      <ul> 
        <li>Use the filters to keep only a set of transactions that should be assigned the same category. Then use the "<em>Set all</em>" and "<em>Validate page</em>" to set all categories at once.</li>
        <li>Transactions for which the ML model has a high confidence (>90%) can likely be tagged directly without checking the transaction metadata.</li>
      </ul>

      <h2 class="subtitle">Machine learning models</h2>
      <p>See <router-link :to="{name: 'models'}">model page</router-link></p>
      <p>
        This page can be used to trigger the training of a machine learning model for classifying transactions. Machine learning models are currently <br/>
        supported for transactions from Belfius CSV only. To train a machine learning model, at least 50 transactions must have been tagged beforehand <br/>
        (ideally with several transactions labeled per category).
      </p>
    </section>
  </div>  
</template>

<script>
export default {

}
</script>

<style>

</style>