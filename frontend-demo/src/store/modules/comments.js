import axios from 'axios';

const state = {
    comments: []
};

const getters = {
    allComments: (state) => state.comments
};

const actions = {
    async fetchComments({ commit }) {
        const response = await axios.get('https://jsonplaceholder.typicode.com/comments');

        commit('setComments', response.data);
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