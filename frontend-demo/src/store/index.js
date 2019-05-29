import Vuex from 'vuex'
import Vue from 'vue'
import Service from '../api/db'

// Load Vuex
Vue.use(Vuex);

const state = {
    label: 'argumentsused',
    currentJWT: ''
};

const getters = {
    jwt: state => state.currentJWT,
    jwtData: (state, getters) => state.currentJWT ? JSON.parse(atob(getters.jwt.split('.')[1])) : null,
    jwtSubject: (state, getters) => getters.jwtData ? getters.jwtData.sub : null,
    jwtIssuer: (state, getters) => getters.jwtData ? getters.jwtData.iss : null
};

const actions = {
    async fetchJWT({ commit }, { username, password }) {
        // TODO: User real endpoint
        // const { data, state } = await Service.get(`login?username=${username}&password=${password}`);
        // commit('setJWT', data);
    }
};

const mutations = {
    setCurrentLabel: (state, label) => (state.label = label),
    setJWT: (state, jwt) => (state.currentJWT = jwt)
};

// Create store
export default new Vuex.Store({
    state,
    getters,
    actions,
    mutations
});
