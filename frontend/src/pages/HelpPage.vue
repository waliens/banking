<template>
  <div class="content">
    <section>
      <h1 class="title">Help page</h1>
      <h2 class="subtitle">Adding transactions</h2>
      <h3 class="subtitle">Data upload</h3>
      <p>See <router-link :to="{name: 'upload-data'}">upload page</router-link> </p>
      <p>The app requires that you upload data to work with. Currently, two import file formats are supported: </p>
      <ul>
        <li>Belfius CSV file (more info <a href="https://www.belfius.be/webapps/fr/selfcare/belfius/comptes/solde-historique/Comment-exporter-mon-historique-vers-un-fichier-CSV-(Excel)-en-Belfius-Direct-Net-">here</a>)</li>
        <li>ING CSV file</li>
        <li>Mastercard spending monthly statement (PDF file from Belfius)</li> 
      </ul>
      <p>
        The upload system is robust enough to support upload of duplicate transactions (see <a href="#help-duplicate-transactions">below</a>). It also attempts to auto-detect and  <br/>
        merge accounts with different names but same number (e.g. matching legacy belgian account numbers with IBAN if necessary). <br /> 
        Merging account is useful for machine learning (see section <em>Machine learning models</em>). Accounts which were not auto-merge 
        can also be merged manually on the <router-link :to="{name: 'merge-accounts'}">merging page</router-link>.
      </p>
      <p><em>Note:</em> the mastercard PDF upload requires you to also associate the credit card account.</p>
      <h3 class="subtitle">Manual transactions</h3>
      <p>See <router-link :to="{name: 'create-transaction'}">create transaction page</router-link></p>
      <p>
        Upload is not the only way one can add transactions to the application. It is also possible to add transactions manually.<br />
        Manual transaction are the only transactions of the platform that can be edited.
      </p>
      <h3 class="subtitle" id="help-duplicate-transactions">Duplicate transactions</h3>
      <p>
        A duplicate transaction is a transaction that appears several times in the database. The application attempts to automatically <br />
        prevent the creation of duplicate. This is done for instance by making upload idempotent, i.e. re-uploading several times the same <br />
        transaction file (csv, pdf, etc.) does not create duplicate transactions. 
      </p>
      <p>
        Unfortunately, it is not always possible to automatically prevent the creation of duplicates. For instance, if a transaction is uploaded <br />
        twice with two different files from two different banks, the information provided in these files do not allow to identify them as identical. <br />
        To mitigate this issue, the application will automatically mark as duplicate any two transactions that match all of the following conditions:
        <ul>
          <li>they involve the exact same amount of money</li>
          <li>they originate same source account</li>
          <li>they target same destination account</li>
          <li>they were accounted on the same date</li>
        </ul>
        This ruleset is not perfect as it can falsly flag a transaction as duplicate that is not (false positive). It can also miss actual <br />
        duplicates (e.g. when the two banks have not accounted the transaction on the same day) (false negative). The application provides <br />
        tools to deal with these false positives and negatives. <router-link :to="{name: 'manage-duplicate-transactions'}">This page</router-link> allows to manually unflag false positives. In the <router-link :to="{name: 'transactions-tagging'}">transactions labeling page</router-link>, <br />
        false negative transactions can manually be marked as duplicates.  
      </p>
      <h3 class="subtitle">Initial account balance</h3>
      <p>
        As it is not always possible to upload the entire transaction history of an account, its balance will not be equal to its real balance by default. <br/>
        To correct the difference, it is possible to add an <em>initial amount</em> in the account edition page. The amount can be positive or negative.
      </p>

      <h2 class="subtitle">Profiles</h2>
      <p>See <router-link :to="{name: 'select-account-group'}">profile page</router-link></p>
      <p>
        A profile is a set of accounts. It can be seen as a system with internal transactions and boundary transactions flowing in and out. <br/>
        Some report features on the app will only consider transactions crossing the boundaries of this system (e.g. incomes and expenses).
      </p>
      <p>
        A profile must be created to access the reporting features of the app (it can contain only one account if necessary). <br/>
        After creation, the profile must be selected which gives access to the reporting page. 
      </p>
      <p>
        A transaction must be explicitely associated to a profile for this transaction to be considered in the different profile-related <br />
        pages. Association of transactions and profiles are automated <strong>ONLY on two occasions</strong>: 
        <ul>
          <li>The transaction is added to the app and is involved with one of the accounts of a profile, this transaction is automatically associated to the profile</li>
          <li>A group is created, all transactions involved with at least one account of the profile are associated with this profile</li>
        </ul>
        In any other case, the transaction must be manually associated to the currently selected profile in the <router-link :to="{name: 'transactions-tagging'}">transactions labeling page</router-link>.
      </p>

      <h2 class="subtitle">Reporting</h2>
      <p> See <router-link :to="{name: 'dashboard'}">report (dashboard) page</router-link></p>
      <p>When an account group has been selected, reports regarding this group can be found on the dashboard page including:</p>
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
        The app provides a labeling page for making easier to label the uploaded transactions. This page provides a filterable <br/>
        list of transactions and different tools for labeling individual transactions or a batch of transaction. A machine <br />
        learning model can be used to suggest labels (see section <em>Machine learning models</em>).
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