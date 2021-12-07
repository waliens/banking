<template>
  <div id="app" class="page-container">
    <layout-navbar></layout-navbar>

    <div class="app-content">
      <router-view v-if="initialized"></router-view>
    </div>

    <layout-footer></layout-footer>
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
  created() {
    this.$store.dispatch('initializeStore');
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
