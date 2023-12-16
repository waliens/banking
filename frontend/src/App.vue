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
import constants from '@/utils/constants.js';
import axios from 'axios';

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
    // fetch configuration for API URL
    let settings;
    await axios
      .get('configuration.json')
      .then(response => (settings = response.data));

    for (let i in settings) {
      constants[i] = settings[i];
    }
    Object.freeze(constants);

    this.$store.dispatch('initializeStore');
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
