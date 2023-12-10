<template>
  <section>
    <h1 class="title">{{ $t('login.title') }}</h1>
    <b-field :label="$t('user.username')" label-position="on-border">
      <b-input v-model="username"></b-input>
    </b-field>
    <b-field :label="$t('user.password')" label-position="on-border">
      <b-input v-model="password" type="password" password-reveal></b-input>
    </b-field>
    <b-field>
      <b-button :label="$t('login.title')" type="is-primary" @click="login"></b-button>
    </b-field>
  </section>
</template>
  
<script>
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
  data() {
    return {
      username: "",
      password: ""
    }
  },
  computed: {
    next() {
      return this.$route.query.next || {name: 'home'};
    }
  },
  methods: {
    async login() {
      await this.$store.dispatch('login', this.getCredentials()).then(() => {
        this.$router.push(this.next);
      }).catch(() => {
        this.$buefy.toast.open({
          message: this.$t('login.invalid-username-or-password'),
          type: 'is-danger'
        });
      })
    },
    getCredentials() {
      return {
        "password": this.password,
        "username": this.username
      }
    }
  }
})
</script>

