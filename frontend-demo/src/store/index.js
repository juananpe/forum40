import Vuex from 'vuex'
import Vue from 'vue'

// Load Vuex
Vue.use(Vuex);

const state = {
    label: 'argumentsused'
};

const getters = {
    currentLabel: (state) => state.label
};

const actions = {};

const mutations = {
    setCurrentLabel: (state, label) => (state.label = label)
};

// Create store
export default new Vuex.Store({
    state,
    getters,
    actions,
    mutations
});
