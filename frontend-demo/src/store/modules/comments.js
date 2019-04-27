import axios from 'axios';
import Service from "../../api/db";

const state = {
    comments: []
};

const getters = {
    allComments: (state) => state.comments
};

const actions = {
    async fetchComments({ commit }) {
        Service.get("db/comments", (status, data) => {
            this.comments = data;
            commit('setComments', data);
        });
    }
};

const mutations = {
    setComments: (state, comments) => (state.comments = comments)
};

export default {
    state,
    getters,
    actions,
    mutations
}