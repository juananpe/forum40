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
        // TODO 
        Service.get("db/comments/" + state.label + "/0/10", (status, data) => {
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