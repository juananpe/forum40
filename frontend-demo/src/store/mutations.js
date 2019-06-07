import {Mutations} from './const'

export default {
    [Mutations.setSelectedLabels]: (state, selection) => (state.selectedLabels = selection),
    [Mutations.setJWT]: (state, jwt) => (state.currentJWT = jwt),
    [Mutations.updateTime]: (state) => (state.now = new Date()),
    [Mutations.setSelectedComment]: (state, comment) => (state.selectedComment = comment)
}