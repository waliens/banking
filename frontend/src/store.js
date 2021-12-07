import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import axios from 'axios';
import AccountGroup from '@/utils/api/AccountGroup';

const state = {
  currentGroup: null,
  initialized: false,
  socketInitialized: false
};

const mutations = {
  setInitialized(state) {
    state.initialized = true;
  },

  setCurrentGroup(state, group) {
    state.currentGroup = group;
  },
};

const actions = {
  async initializeStore({state, commit, dispatch}) {
    if(state.initialized) {
      return;
    }

    state.currentGroup = null;
    commit('setInitialized');
  }
};

const store = new Vuex.Store({
  state,
  mutations,
  actions,
  strict: process.env.NODE_ENV !== 'production'
});

export default store;
