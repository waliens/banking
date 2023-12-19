import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import axios from 'axios';
import Group from '@/utils/api/Group';
import User from '@/utils/api/User';

const state = {
  currentGroupId: null,
  currentGroup: null,
  initialized: false,
  currentUser: null
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
  },
};

const actions = {
  async initializeStore({state, commit, dispatch}) {
    if(state.initialized) {
      return;
    }

    let accessToken = window.localStorage.accessToken;
    let refreshToken = window.localStorage.refreshToken;
    if(!refreshToken || !accessToken) {
      cleanAuthenticationState();
      commit('setInitialized');
      return;
    }
    setAccessToken(accessToken);
    setRefreshToken(refreshToken);
    await dispatch('fetchUser');

    let groupId = window.localStorage.currentGroupId;
    if(!groupId || groupId == "undefined") {
      commit('setInitialized');
      return;
    }

    await dispatch('fetchGroup', groupId);
    commit('setInitialized');
  },

  async login({dispatch}, {username, password}) {
    let {access_token, refresh_token} = await User.login(username, password);
    setRefreshToken(refresh_token);
    setAccessToken(access_token);
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

function setAccessToken(token) {
  window.localStorage.accessToken = token;
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

function setRefreshToken(token) {
  window.localStorage.refreshToken = token;
}

function cleanAuthenticationState() {
  window.localStorage.removeItem('accessToken');
  window.localStorage.removeItem('refreshToken');
  delete axios.defaults.headers.common['Authorization'];
}

const store = new Vuex.Store({
  state,
  mutations,
  actions,
  strict: process.env.NODE_ENV !== 'production'
});

export default store;
