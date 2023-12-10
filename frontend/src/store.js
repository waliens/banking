import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import axios from 'axios';
import Group from '@/utils/api/Group';
import User from '@/utils/api/User';

const state = {
  currentGroupId: null,
  currentGroup: null,
  initialized: false
};

const mutations = {
  setInitialized(state) {
    state.initialized = true;
  },

  setCurrentUser(state, user) {
    state.currentUser = user;
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

    let token = window.localStorage.accessToken;
    if(token == null) {
      commit('setInitialized');
      return;
    }

    let groupId = window.localStorage.currentGroupId;
    if(!groupId || groupId == "undefined") {
      commit('setInitialized');
      return;
    }

    await dispatch('fetchGroup', groupId);
    commit('setInitialized');
  },

  async login({dispatch}, {username, password}) {
    let token = await User.login(username, password);
    console.log(token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    console.log(axios.defaults.headers);
    window.localStorage.accessToken = token;
    await dispatch('fetchUser');
  },

  async fetchUser({commit}) {
    let user = null;

    try {
      user = await User.fetchCurrent();
    }
    catch (e) {
      console.log('Error while fetching current user.');

      cleanAuthenticationState();
      commit('setCurrentUser', null);
      return;
    }

    commit('setCurrentUser', user);
  },

  logout({commit}) {
    cleanAuthenticationState();
    commit('setCurrentUser', null);
  },

  setCurrentGroup({commit}, group) {
    commit('setCurrentGroup', group);
  },

  async fetchGroup({commit, dispatch}, groupId) {
    if (!groupId) {
      return;
    }
    let group = null;

    try {
      group = await Group.fetch(groupId);
    }
    catch (e) {
      console.log('Error while fetching group.');
      commit('clearCurrentGroup');
      return;
    }

    dispatch('setCurrentGroup', group);
  }
};

function cleanAuthenticationState() {
  delete axios.defaults.headers.common['Authentication'];
}


const store = new Vuex.Store({
  state,
  mutations,
  actions,
  strict: process.env.NODE_ENV !== 'production'
});

export default store;
