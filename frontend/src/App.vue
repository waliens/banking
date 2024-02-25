<template>
  <div id="app" class="page-container">
    <div v-if="initialized">
      <layout-navbar></layout-navbar>

      <div class="app-content">
        <router-view></router-view>
      </div>

      <layout-footer></layout-footer>
    </div>
  </div>
</template>

<script>
import LayoutNavbar from './components/layout/LayoutNavbar';
import LayoutFooter from './components/layout/LayoutFooter';

export default {
  name: 'App',
  components: {
    LayoutNavbar,
    LayoutFooter
  },
  computed: {
    initialized() {
      return this.$store.state.initialized;
    }
  },
  async created() {
    await this.$store.dispatch('initializeStore');
    setInterval(async () => {
      let token = await this.$store.dispatch('checkTokenRefresh');
      if (!token) {
        this.$router.push({name: 'login'});
      }
    }, 60 * 1000); // refresh token every 60sec
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
}

.app-content {
  margin: 10px;
}
</style>
