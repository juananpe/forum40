import Vuex from 'vuex'
import Vue from 'vue'
import Service from '../api/db'
import axios from 'axios'

Vue.use(Vuex);


const state = {
    label: 'argumentsused',
    currentJWT: ''
};

const getters = {
    jwt: state => state.currentJWT,
    jwtData: (state, getters) => state.currentJWT ? JSON.parse(atob(getters.jwt.split('.')[1])) : null,
    jwtUser: (state, getters) => state.currentJWT ? getters.jwtData.user : null,
    jwtExpiration: (state, getters) => getters.jwtData ? getters.jwtData.exp : null,
    jwtLoggedIn: (state, getters) => getters.jwt && getters.jwtExpiration * 1000 >= Date.now()
};

const actions = {
    async fetchJWT({ commit }, { username, password }) {
        // TODO: User real endpoint
        try {
            const { data } = await Service.get(`db/auth/login/${username}/${password}`);
            commit('setJWT', data.token);
            return true;
        }
        catch (error) {
            const status = error.response.status;
            if (status === 401) {
                return false;
            }
        }
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
