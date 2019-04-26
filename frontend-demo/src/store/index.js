import Vuex from 'vuex'
import Vue from 'vue'
import comments from './modules/comments'

// Load Vuex
Vue.use(Vuex);

// Create store
export default new Vuex.Store({
    modules: {
        comments
    }
});
