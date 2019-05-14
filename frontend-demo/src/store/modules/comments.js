import axios from 'axios';
import Service from "../../api/db";

const state = {
    comments: [],
    label: 'argumentsused'
};

const getters = {
    allComments: (state) => state.comments,
    currentLabel: (state) => state.label
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
    setComments: (state, comments) => (state.comments = comments),
    setCurrentLabel: (state, label) => (state.label = label)
};

export default {
    state,
    getters,
    actions,
    mutations
}