import Vuex from 'vuex'
import VuexPersist from 'vuex-persist';
import Vue from 'vue'

import { State, Mutations } from './const'
import getters from './getters'
import mutations from './mutations'
import actions from './actions'

Vue.use(Vuex);


const state = {
    [State.labels]: [],
    [State.source]: "",
    [State.sources]: [],
    [State.selectedFilters]: {
        [State.selectedLabels]: [],
        [State.keywordfilter]: ''
    },
    [State.selectedViewAggregations]: {
        [State.timeFrequency] : 'm'
    },
    [State.selectedComment]: {},
    [State.currentJWT]: '',
    [State.now]: new Date(),
    [State.refreshTokenInterval]: null
};

const syncedMutations = [
    Mutations.setJWT
]

const vuexLocalStorage = new VuexPersist({
    key: 'vuex',
    storage: window.localStorage,
    reducer: state => ({ currentJWT: state.currentJWT }),
    filter: mutation => (syncedMutations.indexOf(mutation.type) !== -1)
});

// Create store
export default new Vuex.Store({
    state,
    getters,
    actions,
    mutations,
    plugins: [vuexLocalStorage.plugin]
});
