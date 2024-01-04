<template>
  <b-navbar class="is-primary">
    <template #brand>
      <b-navbar-item tag="router-link" :to="{ name: 'dashboard' }">
        <strong>{{$t("app_name")}}</strong>
      </b-navbar-item>
    </template>
    <template #start v-if="loggedIn">
      <b-navbar-item tag="router-link" :to="{ name: 'select-account-group' }">
        <span><b-icon icon="user"/> {{$t('account_group.groups')}}</span>
      </b-navbar-item>
      <b-navbar-item tag="router-link" :to="{ name: 'transactions-tagging' }">
        <span><b-icon icon="tag"/> {{$t('tagging.title')}}</span>
      </b-navbar-item>
      <b-navbar-dropdown>
        <template #label>
          <span><b-icon icon="plus"/> {{$t('transaction.title')}}</span>
        </template>
        <b-navbar-item tag="router-link" :to="{ name: 'upload-data' }">
          <span><b-icon icon="upload"/> {{$t('data_upload.title')}}</span>
        </b-navbar-item>
        <b-navbar-item tag="router-link" :to="{ name: 'create-transaction' }">
          <span><b-icon icon="hand-paper"/> {{$t('data_upload.manual')}}</span>
        </b-navbar-item>
      </b-navbar-dropdown>
      <b-navbar-dropdown>
        <template #label>
          <span><b-icon icon="pen"/> {{ $t('navbar.data') }}</span>
        </template>
        <b-navbar-item tag="router-link" :to="{ name: 'edit-tag-tree' }">
          <span><b-icon icon="sitemap"/> {{$t('tagging.tree')}} </span>
        </b-navbar-item>
        <b-navbar-item tag="router-link" :to="{ name: 'merge-accounts' }">
          <span><b-icon icon="random" /> {{$t('account.merge')}}</span>
        </b-navbar-item>
        <b-navbar-item tag="router-link" :to="{ name: 'models' }">
          <span><b-icon icon="hat-wizard"/> {{$t('ml_model.title')}}</span>
        </b-navbar-item>
        <b-navbar-item tag="router-link" :to="{ name: 'manage-duplicate-transactions' }">
          <span><b-icon icon="copy"/> {{$t('navbar.manage_duplicate')}} </span>
        </b-navbar-item>
      </b-navbar-dropdown>
      <b-navbar-item tag="router-link" :to="{ name: 'help' }">
        <span><b-icon icon="question-circle"/> {{$t("help")}}</span>
      </b-navbar-item>
    </template>
    <template #end>

        <b-navbar-item tag="router-link" :to="{ name: 'select-account-group' }" v-if="loggedIn">
          <div class="group info">
            <b-tag :type="group_tag_class">{{$t('profile')}}: <em>{{!!group ? group.name : $t('account_group.not_selected')}}</em></b-tag>
          </div>
        </b-navbar-item>

        <b-navbar-dropdown v-if="loggedIn">
          <template #label>
            <b-tag type="is-info" >
              {{ $t('login.user') }}: {{ $store.state.currentUser.username }}
            </b-tag>
          </template>
          <b-navbar-item tag="router-link" :to="{ name: 'manage-users' }">{{ $t('users.manage') }}</b-navbar-item>
          <b-navbar-item @click="logout">{{ $t('logout.title') }}</b-navbar-item>
        </b-navbar-dropdown>
        <b-navbar-item v-else> <b-tag type="is-danger" >{{ $t('login.not_loggedin') }}</b-tag></b-navbar-item>

    </template>
  </b-navbar>
</template>

<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  computed: {
    group() {
      return this.$store.state.currentGroup;
    },
    group_tag_class() {
      if (this.group) {
        return "is-success";
      } else{
        return "is-warning";
      }
    },
    login_tag_class() {
      if (this.$store.state.currentUser) {
        return "is-info";
      } else{
        return "is-danger";
      }
    },
    loggedIn() {
      return !!this.$store.state.currentUser;
    }
  },
  methods: {
    logout() {
      this.$store.dispatch('logout');
      this.$router.push({'name': 'login'});
    }
  }
})
</script>

<style lang="scss">
@import "@/assets/colors.scss";
#brand, #end {
  background-color: $primary;
}
</style>