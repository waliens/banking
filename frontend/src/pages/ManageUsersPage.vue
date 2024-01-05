<template>
  <div class="columns">
    <section class="column is-one-quarter">
      <b-menu class="scrollable" :label="$t('users.title')">
        <b-menu-list >
          <template #label>
            <section class="level">
              <div class="level-item">{{$t('users.title')}}</div>
              <div class="level-item">
                <b-button class="is-small" type="is-primary" icon-left="plus" @click="addNewUser" :disabled="isAnyUserInMenuNotSaved"></b-button>
              </div>
            </section>
          </template>
          <b-menu-item v-for="(user, index) in users" :key="user.id" :active.sync="activeItems[index]">
            <template #label>
              <b-icon icon="user" />
              <span v-if="!user.id"><em> {{ user.username }} </em></span>
              <span v-else> {{ user.username }} </span>
            </template>
          </b-menu-item>
        </b-menu-list>
      </b-menu>
    </section>
    <section class="column">
      <section class="level title-section">
        <div class="level-left">
          <h3 class="title">
            <span v-if="activeUser && activeUser.id">{{ $t('user.edit') }}</span>
            <span v-else>{{ $t('user.create') }}</span>
          </h3>
        </div>
        <div class="level-right">
          <b-button :disabled="!isFormValid()" class="is-small is-primary" @click="saveUser" icon-right="save">{{$t('save')}}</b-button>
        </div>
      </section>
      <section v-if="isAnyUserMenuActive">
        <b-field :label="$t('user.username')" label-position="on-border" :type="activeUser.username.length > 0 ? '' : 'is-danger'">
          <b-input v-model="activeUser.username"></b-input>
        </b-field>
        <b-field :label="$t('user.password')" label-position="on-border" :type="passwordDoMatch ? '' : 'is-danger'">
          <b-input type="password" password-reveal v-model="activeUser.password"></b-input>
        </b-field>
        <b-field :label="$t('user.repeat_password')" label-position="on-border" :type="passwordDoMatch ? '' : 'is-danger'">
          <b-input type="password" password-reveal v-model="activeUser.password2"></b-input>
        </b-field>
      </section>
    </section>
  </div>
</template>

<script>
import { defineComponent } from '@vue/composition-api'
import User from '@/utils/api/User';

export default defineComponent({
  name: "ManageUserPage",
  data() {
    return {
      users: [],
      activeItems: [],
    }
  },
  async created() {
    await this.fetchUsers();
  },
  computed: {
    isAnyUserMenuActive() {
      return !this.activeItems.every(b => !b);
    },
    isAnyUserInMenuNotSaved() {
      return !this.users.every(u => !!u.id);
    },
    activeUser() {
      for (let i = 0; i < this.activeItems.length; ++i) {
        if (this.activeItems[i]) {
          return this.users[i];
        }
      }
      return null;
    },
    passwordDoMatch() {
      return this.activeUser && this.activeUser.password == this.activeUser.password2;
    }
  },
  methods: {
    async fetchUsers() {
      this.users = await User.fetchAll();
      if (this.users) {
        this.resetActive();
      }
    },
    resetActive() {
      this.activeItems = Array(this.users.length).fill(false);
    },
    addNewUser() {
      let user = new User();
      user.username = "???";
      this.users.push(user);
      this.resetActive();
      this.activeItems[this.activeItems.length - 1] = true;
    },
    isFormValid(){
      if (!this.activeUser) {
        return false;
      }
      return this.passwordDoMatch && this.activeUser && this.activeUser.username.length > 0;
    },
    async saveUser() {
      // empty password fields
      this.activeUser.password2 = undefined;
      await this.activeUser.save();
      this.activeUser.password = undefined;
      this.resetActive();
    }
  },
  watch: {
    activeItems: {
      handler: function () {
        if (!this.isAnyUserMenuActive) {
          return;
        }
        this.activeUser
      },
      deep: true
    }
  },
})
</script>

