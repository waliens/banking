import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import axios from 'axios';
import moment from 'moment';

import constants from '@/utils/constants.js';
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
    window.localStorage.removeItem("currentGroupId");
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
    let refreshTokenStoredAt = window.localStorage.refreshTokenStoredAt;
    if(!refreshToken || !accessToken || !refreshTokenStoredAt || moment(refreshTokenStoredAt).diff(moment(), 'months') >= 1) {
      cleanAuthenticationState();
      commit('setInitialized');
      return;
    }

    initAxiosToken(accessToken);
    await dispatch('fetchUser');

    let groupId = window.localStorage.currentGroupId;
    if(!groupId) {
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

  /**
   * @returns null if refresh was not possible, a valid 'recent' access token 
   */
  async checkTokenRefresh() {
    if (!window.localStorage.accessTokenStoredAt) {
      return null;
    }
    let accessTokenStoredAt = moment(window.localStorage.accessTokenStoredAt)
    if (moment().diff(accessTokenStoredAt, 'minutes') >= 30) { // after 30 minutes, refresh
      return await doRefreshToken();
    }
    return window.localStorage.accessToken;
  },

  async fetchUser({commit}) {
    let user = null;

    try {
      user = await User.fetchCurrent();
    } catch (e) {
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

export async function doRefreshToken() {
  let refreshToken = window.localStorage.refreshToken;
  if (!refreshToken) {
    return null;
  }
  let refreshTokenStoredAt = moment(window.localStorage.refreshTokenStoredAt);
  if (refreshTokenStoredAt.diff(moment(), 'months') >= 1) {
    cleanAuthenticationState();
    return null;
  }
  return await axios.post(
    `${window.location.origin}/${constants.API_PREFIX}refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    }
  ).then(({data}) => {
    setAccessToken(data.access_token);
    return data.access_token;
  }).catch(() => {
    console.error("could not refresh token");
    return null;
  });
}

function initAxiosToken(accessToken) {
  axios.defaults.headers.common['Authorization'] = accessToken ? `Bearer ${accessToken}` : undefined;
}

function setAccessToken(token) {
  if (!token) {
    window.localStorage.removeItem('accessTokenStoredAt');
    window.localStorage.removeItem('accessToken');
  } else {
    window.localStorage.accessToken = token;
    window.localStorage.accessTokenStoredAt = moment().toISOString();
  }
  initAxiosToken(token);
}

function setRefreshToken(token) {
  if (!token) {
    window.localStorage.removeItem('refreshTokenStoredAt');
    window.localStorage.removeItem('refreshToken');
  } else {
    window.localStorage.refreshToken = token;
    window.localStorage.refreshTokenStoredAt = moment().toISOString();
  }
}

function cleanAuthenticationState() {
  window.localStorage.removeItem('accessToken');
  window.localStorage.removeItem('accessTokenStoredAt');
  window.localStorage.removeItem('refreshToken');
  window.localStorage.removeItem('refreshTokenStoredAt');
  delete axios.defaults.headers.common['Authorization'];
}

const store = new Vuex.Store({
  state,
  mutations,
  actions,
  strict: process.env.NODE_ENV !== 'production'
});

export default store;
