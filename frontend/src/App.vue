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
import { doRefreshToken } from './store.js';

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
    setInterval(doRefreshToken, 30 * 1000 * 3600); // refresh token every 30min
    await this.$store.dispatch('initializeStore');
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
