import Vuex from 'vuex'
import VuexPersist from 'vuex-persist';
import Vue from 'vue'
import Service from '../api/db'
import Const from '../const'

Vue.use(Vuex);


const state = {
    label: 'argumentsused',
    currentJWT: '',
    now: new Date(),
    refreshTokenInterval: null
};

const getters = {
    jwt: state => state.currentJWT,
    jwtData: (state, getters) => state.currentJWT ? JSON.parse(atob(getters.jwt.split('.')[1])) : null,
    jwtUser: (state, getters) => state.currentJWT ? getters.jwtData.user : null,
    jwtExpiration: (state, getters) => getters.jwtData ? getters.jwtData.exp : null,
    jwtLoggedIn: (state, getters) => getters.jwt && getters.jwtExpiration * 1000 >= state.now
};

const actions = {
    async login({ commit, getters, state, dispatch }, { username, password }) {
        try {
            const { data } = await Service.get(`db/auth/login/${username}/${password}`);
            commit('setJWT', data.token);
            state.refreshTokenInterval = setInterval(() => {
                if ((getters.jwtExpiration * 1000 - state.now) <= Const.refreshTokenBefore)
                    dispatch('refreshToken');
            }, Const.refreshTokenCheckInterval);
            return true;
        }
        catch (error) {
            const status = error.response.status;
            if (status === 401) {
                return false;
            }
        }
    },
    async refreshToken({ commit, state }) {
        const { data } = await Service.get('db/auth/refreshToken', state.currentJWT);
        if (data.token) {
            commit('setJWT', data.token);
            return true;
        }
        return false;
    },
    async logout({ commit, state }) {
        const { data } = await Service.get('db/auth/logout', state.currentJWT);
        if (data.logout === "ok") {
            commit('setJWT', '');
            clearInterval(state.refreshTokenInterval);
        }
    },
    start({ commit }) {
        setInterval(() => {
            commit('updateTime')
        }, Const.updateNowInterval)
    }
};

const mutations = {
    setCurrentLabel: (state, label) => (state.label = label),
    setJWT: (state, jwt) => (state.currentJWT = jwt),
    updateTime: (state) => (state.now = new Date())
};

const notSyncedMutations = [
    'setCurrentLabel',
    'updateTime'
]

const vuexLocalStorage = new VuexPersist({
    key: 'vuex',
    storage: window.localStorage,
    reducer: state => ({ currentJWT: state.currentJWT }),
    filter: mutation => (notSyncedMutations.indexOf(mutation.type) === -1)
});

// Create store
export default new Vuex.Store({
    state,
    getters,
    actions,
    mutations,
    plugins: [vuexLocalStorage.plugin]
});
