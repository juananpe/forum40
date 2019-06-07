import { State, Mutations } from './const'

export default {
    [Mutations.setJWT]: (state, jwt) => (state[State.currentJWT] = jwt),
    [Mutations.updateTime]: (state) => (state[State.now] = new Date()),
    [Mutations.setSelectedComment]: (state, comment) => (state[State.selectedComment] = comment),
    [Mutations.setSelectedLabels]: (state, selection) => (state[State.selectedFilters][State.selectedLabels] = selection),
    [Mutations.setKeywordfilter]: (state, keyword) => (state[State.selectedFilters][State.keywordfilter] = keyword)
}