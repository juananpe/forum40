import { State, Getters } from './const'

export default {
    [Getters.jwt]: state => state.currentJWT,
    [Getters.jwtData]: (state, getters) => state.currentJWT ? JSON.parse(atob(getters.jwt.split('.')[1])) : null,
    [Getters.jwtUser]: (state, getters) => state.currentJWT ? getters.jwtData.user : null,
    [Getters.jwtExpiration]: (state, getters) => getters.jwtData ? getters.jwtData.exp : null,
    [Getters.jwtLoggedIn]: (state, getters) => !getters.jwt.isEmpty && (getters.jwtExpiration || 0) * 1000 >= state.now,
    [Getters.labelParameters]: (state) => Object.values(state[State.selectedFilters][State.selectedLabels]).map((label_id) => `label=${label_id}`).join('&'),
    [Getters.selectedCommentId]: (state) => Object.entries(state.selectedComment).length !== 0 ? state.selectedComment.comment_id : null,
    [Getters.selectedLabels]: (state) => Object.keys(state[State.selectedFilters][State.selectedLabels]),
    [Getters.keywordfilter]: (state) => state[State.selectedFilters][State.keywordfilter],
    [Getters.activeFilters]: (state) => Object.keys(state[State.selectedFilters]).filter(e => state[State.selectedFilters][e] && state[State.selectedFilters][e].length > 0),
    [Getters.timeFrequency]: (state) => state[State.selectedViewAggregations][State.timeFrequency],
}