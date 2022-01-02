import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import AccountGroup from '@/utils/api/AccountGroup';

const state = {
  currentGroupId: null,
  currentGroup: null,
  initialized: false
};

const mutations = {
  setInitialized(state) {
    state.initialized = true;
  },

  setCurrentGroup(state, group) {
    window.localStorage.currentGroupId = group.id;
    state.currentGroupId = group.id;
    state.currentGroup = group;
  },

  clearCurrentGroup(state) {
    window.localStorage.currentGroupId = undefined;
    state.currentGroupId = null;
    state.currentGroup = null;
  }
};

const actions = {
  async initializeStore({state, commit, dispatch}) {
    if(state.initialized) {
      return;
    }

    let groupId = window.localStorage.currentGroupId;
    if(!groupId) {
      commit('setInitialized');
      return;
    }

    await dispatch('fetchGroup', groupId);
    commit('setInitialized');
  },

  setCurrentGroup({commit}, group) {
    commit('setCurrentGroup', group);
  },

  async fetchGroup({commit, dispatch}, groupId) {
    if (!groupId) {
      console.log("not set");
      return;
    }
    let group = null;

    try {
      group = await AccountGroup.fetch(groupId);
    }
    catch (e) {
      console.log('Error while fetching group.');
      commit('clearCurrentGroup');
      return;
    }

    dispatch('setCurrentGroup', group);
  }
};

const store = new Vuex.Store({
  state,
  mutations,
  actions,
  strict: process.env.NODE_ENV !== 'production'
});

export default store;
